"""Profile domain — view/update own profile and the public seller profile."""

from __future__ import annotations

from datetime import datetime, timezone

from bson import ObjectId
from pymongo import DESCENDING

from shared.errors import NotFound
from shared.mongo import COLLECTIONS
from shared.roles import Role

from .serializers import iso, user_summary


def now() -> datetime:
    return datetime.now(timezone.utc)


def me(db, user: dict) -> dict:
    rating = user.get("rating") or {"avg": 0, "count": 0}
    listing_count = db[COLLECTIONS["listings"]].count_documents(
        {"seller": user["_id"], "status": {"$ne": "deleted"}}
    )
    return {
        "id": str(user["_id"]),
        "name": user.get("name", ""),
        "email": user.get("email", ""),
        "role": user.get("role", Role.BUYER),
        "phone": user.get("phone", ""),
        "bio": user.get("bio", ""),
        "location": user.get("location") or {},
        "status": user.get("status", "active"),
        "rating": rating,
        "listing_count": listing_count,
        "created_at": iso(user.get("created_at")),
    }


def update(db, user: dict, data: dict) -> dict:
    payload: dict = {}
    if data.get("name"):
        payload["name"] = data["name"].strip()
    if data.get("phone") is not None:
        payload["phone"] = data["phone"]
    if data.get("bio") is not None:
        payload["bio"] = data["bio"]
    if data.get("location_city"):
        payload["location.city"] = data["location_city"]

    if payload:
        payload["updated_at"] = now()
        db[COLLECTIONS["users"]].update_one({"_id": user["_id"]}, {"$set": payload})

    fresh = db[COLLECTIONS["users"]].find_one({"_id": user["_id"]})
    return me(db, fresh)


def become_seller(db, user: dict) -> dict:
    if user.get("role") == Role.BUYER:
        db[COLLECTIONS["users"]].update_one(
            {"_id": user["_id"]}, {"$set": {"role": Role.SELLER, "updated_at": now()}}
        )
    fresh = db[COLLECTIONS["users"]].find_one({"_id": user["_id"]})
    return me(db, fresh)


def public_profile(db, user_id: str, limit: int = 12) -> dict:
    try:
        oid = ObjectId(user_id)
    except Exception as exc:
        raise NotFound("user not found") from exc
    user = db[COLLECTIONS["users"]].find_one({"_id": oid})
    if user is None:
        raise NotFound("user not found")

    from .listings import list_listings

    listings = list_listings(db, seller=user_id, page=1, page_size=limit)
    return {
        "user": user_summary(user),
        "bio": user.get("bio", ""),
        "listings": listings["items"],
        "listing_count": listings["total"],
    }