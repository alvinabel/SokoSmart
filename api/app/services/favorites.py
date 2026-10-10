"""Favorites domain — one (user, listing) pair."""

from __future__ import annotations

from datetime import datetime, timezone

from bson import ObjectId
from pymongo import DESCENDING

from shared.errors import NotFound
from shared.mongo import COLLECTIONS

from .listings import get


def now() -> datetime:
    return datetime.now(timezone.utc)


def toggle(db, user: dict, listing_id: str) -> dict:
    get(db, listing_id)  # 404 guard
    pair = {"user": user["_id"], "listing": ObjectId(listing_id)}
    existing = db[COLLECTIONS["favorites"]].find_one(pair)
    if existing:
        db[COLLECTIONS["favorites"]].delete_one({"_id": existing["_id"]})
        return {"favorited": False}
    db[COLLECTIONS["favorites"]].insert_one({**pair, "created_at": now()})
    return {"favorited": True}


def list_favorites(db, user: dict, page: int = 1, page_size: int = 20) -> dict:
    coll = db[COLLECTIONS["favorites"]]
    query = {"user": user["_id"]}
    total = coll.count_documents(query)
    cursor = coll.find(query).sort("created_at", DESCENDING).skip((page - 1) * page_size).limit(page_size)
    items = []
    for fav in cursor:
        listing = db[COLLECTIONS["listings"]].find_one({"_id": fav["listing"]})
        if listing and listing.get("status") != "deleted":
            items.append(
                {
                    "id": str(fav["_id"]),
                    "favorited_at": fav.get("created_at").isoformat() if fav.get("created_at") else None,
                    "listing": _snapshot(db, listing),
                }
            )
    return {"items": items, "total": total, "page": page, "page_size": page_size, "pages": max((total + page_size - 1) // page_size, 1)}


def _snapshot(db, listing: dict) -> dict:
    from .serializers import listing_snapshot

    return listing_snapshot(db, listing)