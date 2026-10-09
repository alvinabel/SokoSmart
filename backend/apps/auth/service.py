"""Auth business logic. Each function operates on a Mongo ``users``/``refresh_tokens`` db handle."""

from __future__ import annotations

from datetime import datetime, timezone

from bson import ObjectId
from jwt import PyJWTError

from shared.errors import Conflict, Forbidden, NotFound, Unauthorized
from shared.jwt_token import create_access_token, create_refresh_token, decode_token
from shared.mongo import COLLECTIONS
from shared.passwords import hash_password, verify_password
from shared.roles import Role


def now() -> datetime:
    return datetime.now(timezone.utc)


def serialize_user(user: dict) -> dict:
    """Public user shape — never exposes ``password_hash``."""
    rating = user.get("rating") or {"avg": 0, "count": 0}
    return {
        "id": str(user["_id"]),
        "name": user.get("name", ""),
        "email": user.get("email", ""),
        "role": user.get("role", Role.BUYER),
        "phone": user.get("phone", ""),
        "location": user.get("location") or {},
        "status": user.get("status", "active"),
        "rating": rating,
        "created_at": user.get("created_at").isoformat() if user.get("created_at") else None,
    }


def _issue_tokens(user: dict, db) -> dict[str, str]:
    """Mint an access + refresh token pair and register the (revocable) refresh jti."""
    access = create_access_token(user)
    refresh, jti = create_refresh_token(str(user["_id"]))
    db[COLLECTIONS["refresh_tokens"]].insert_one(
        {
            "jti": jti,
            "user": str(user["_id"]),
            "revoked": False,
            "created_at": now(),
        }
    )
    return {"access_token": access, "refresh_token": refresh}


def register(data: dict, db) -> dict:
    email = data["email"]
    existing = db[COLLECTIONS["users"]].find_one({"email": email})
    if existing:
        raise Conflict("an account with this email already exists")

    user = {
        "name": data["name"],
        "email": email,
        "password_hash": hash_password(data["password"]),
        "role": data.get("role") if data.get("role") in Role.ALL else Role.BUYER,
        "phone": data.get("phone", ""),
        "location": {},
        "status": "active",
        "verified": False,
        "created_at": now(),
        "updated_at": now(),
    }
    result = db[COLLECTIONS["users"]].insert_one(user)
    user["_id"] = result.inserted_id

    tokens = _issue_tokens(user, db)
    return {"user": serialize_user(user), **tokens}


def login(email: str, password: str, db) -> dict:
    user = db[COLLECTIONS["users"]].find_one({"email": email})
    if user is None or not verify_password(password, user.get("password_hash", "")):
        raise Unauthorized("invalid email or password")

    if user.get("status") == "suspended":
        raise Forbidden("account is suspended")

    tokens = _issue_tokens(user, db)
    return {"user": serialize_user(user), **tokens}


def refresh(refresh_token: str, db) -> dict:
    try:
        claims = decode_token(refresh_token, expected_type="refresh")
    except PyJWTError as exc:
        raise Unauthorized("invalid refresh token") from exc

    stored = db[COLLECTIONS["refresh_tokens"]].find_one({"jti": claims.get("jti")})
    if stored is None or stored.get("revoked"):
        raise Unauthorized("refresh token has been revoked")

    user = db[COLLECTIONS["users"]].find_one({"_id": ObjectId(claims["sub"])})
    if user is None:
        raise Unauthorized("user no longer exists")
    if user.get("status") == "suspended":
        raise Forbidden("account is suspended")

    db[COLLECTIONS["refresh_tokens"]].update_one(
        {"jti": claims.get("jti")}, {"$set": {"revoked": True, "revoked_at": now()}}
    )
    tokens = _issue_tokens(user, db)
    return {"user": serialize_user(user), **tokens}


def logout(user: dict, refresh_token: str, db) -> None:
    """Revoke the presented refresh token (rotation invalidates the old pair)."""
    try:
        claims = decode_token(refresh_token, expected_type="refresh")
    except PyJWTError as exc:
        raise Unauthorized("invalid refresh token") from exc
    db[COLLECTIONS["refresh_tokens"]].update_one(
        {"jti": claims.get("jti")}, {"$set": {"revoked": True, "revoked_at": now()}}
    )


def get_user_or_404(user_id: str, db) -> dict:
    try:
        user = db[COLLECTIONS["users"]].find_one({"_id": ObjectId(user_id)})
    except Exception as exc:  # invalid ObjectId
        raise NotFound("user not found") from exc
    if user is None:
        raise NotFound("user not found")
    return user