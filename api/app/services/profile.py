"""Profile domain — view/update own profile and the public seller profile."""

from __future__ import annotations

from datetime import datetime, timezone

from shared.db import execute, fetch_one
from shared.errors import NotFound
from shared.roles import Role

from .serializers import get_user, iso, user_summary


def now() -> datetime:
    return datetime.now(timezone.utc)


def _shape(db, user: dict) -> dict:
    rating = user.get("rating") or {"avg": 0, "count": 0}
    listing_count = fetch_one(
        db,
        "SELECT count(*) AS n FROM listings WHERE seller_id = %s AND status <> 'deleted'",
        (user["_id"],),
    )["n"]
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


def me(db, user: dict) -> dict:
    return _shape(db, user)


def update(db, user: dict, data: dict) -> dict:
    sets: list[str] = []
    params: list = []
    if data.get("name"):
        sets.append("name = %s")
        params.append(data["name"].strip())
    if data.get("phone") is not None:
        sets.append("phone = %s")
        params.append(data["phone"])
    if data.get("bio") is not None:
        sets.append("bio = %s")
        params.append(data["bio"])
    if data.get("location_city"):
        sets.append("location = jsonb_set(location, '{city}', to_jsonb(%s))")
        params.append(data["location_city"])

    if sets:
        sets.append("updated_at = %s")
        params.extend([now(), user["_id"]])
        execute(db, f"UPDATE users SET {', '.join(sets)} WHERE id = %s", tuple(params))

    return me(db, get_user(db, user["_id"]))


def become_seller(db, user: dict) -> dict:
    if user.get("role") == Role.BUYER:
        execute(
            db,
            "UPDATE users SET role = %s, updated_at = %s WHERE id = %s",
            (Role.SELLER, now(), user["_id"]),
        )
    return me(db, get_user(db, user["_id"]))


def public_profile(db, user_id: str, limit: int = 12) -> dict:
    user = get_user(db, user_id)
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
