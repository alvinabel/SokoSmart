"""Auth business logic.

Runs against the shared PostgreSQL store. A hash created here is verifiable by
the FastAPI service (both use ``shared.passwords``), and refresh tokens are
revocable rows in ``refresh_tokens``.
"""

from __future__ import annotations

from datetime import datetime, timezone

from jwt import PyJWTError

from shared.db import fetch_one, insert_returning
from shared.errors import Conflict, Forbidden, NotFound, Unauthorized
from shared.jwt_token import create_access_token, create_refresh_token, decode_token
from shared.passwords import hash_password, verify_password
from shared.roles import Role

USER_COLS = "id AS _id, name, email, role, phone, bio, location, status, verified, rating, created_at"


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
    insert_returning(
        db,
        "INSERT INTO refresh_tokens (jti, user_id, revoked, created_at) "
        "VALUES (%s, %s, false, %s) RETURNING jti",
        (jti, str(user["_id"]), now()),
    )
    return {"access_token": access, "refresh_token": refresh}


def register(data: dict, db) -> dict:
    email = data["email"]
    if fetch_one(db, "SELECT 1 AS ok FROM users WHERE email = %s", (email,)):
        raise Conflict("email already registered")

    user = insert_returning(
        db,
        f"""
        INSERT INTO users (name, email, password_hash, role, phone, location, status, verified, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, '{{}}'::jsonb, 'active', false, %s, %s)
        RETURNING {USER_COLS}
        """,
        (
            data["name"],
            email,
            hash_password(data["password"]),
            Role.BUYER,
            data.get("phone") or "",
            now(),
            now(),
        ),
    )
    tokens = _issue_tokens(user, db)
    return {"user": serialize_user(user), **tokens}


def login(email: str, password: str, db) -> dict:
    user = fetch_one(db, f"SELECT {USER_COLS}, password_hash FROM users WHERE email = %s", (email,))
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

    stored = fetch_one(db, "SELECT jti, revoked FROM refresh_tokens WHERE jti = %s", (claims.get("jti"),))
    if stored is None or stored.get("revoked"):
        raise Unauthorized("refresh token has been revoked")

    user = fetch_one(db, f"SELECT {USER_COLS} FROM users WHERE id = %s", (claims.get("sub"),))
    if user is None:
        raise Unauthorized("user no longer exists")
    if user.get("status") == "suspended":
        raise Forbidden("account is suspended")

    fetch_one(
        db,
        "UPDATE refresh_tokens SET revoked = true, revoked_at = %s WHERE jti = %s RETURNING jti",
        (now(), claims.get("jti")),
    )
    tokens = _issue_tokens(user, db)
    return {"user": serialize_user(user), **tokens}


def logout(user: dict, refresh_token: str, db) -> None:
    """Revoke the presented refresh token (rotation invalidates the old pair)."""
    try:
        claims = decode_token(refresh_token, expected_type="refresh")
    except PyJWTError as exc:
        raise Unauthorized("invalid refresh token") from exc
    fetch_one(
        db,
        "UPDATE refresh_tokens SET revoked = true, revoked_at = %s WHERE jti = %s RETURNING jti",
        (now(), claims.get("jti")),
    )


def get_user_or_404(user_id: str, db) -> dict:
    user = fetch_one(db, f"SELECT {USER_COLS}, password_hash FROM users WHERE id = %s", (user_id,))
    if user is None:
        raise NotFound("user not found")
    return user
