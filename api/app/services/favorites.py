"""Favorites domain — one per (user, listing) pair."""

from __future__ import annotations

from datetime import datetime, timezone

from shared.db import execute, fetch_all, fetch_one
from shared.errors import NotFound

from .serializers import LISTING_COLS, get_listing_row, listing_snapshot

FAV_COLS = "id AS _id, user_id AS user, listing_id AS listing, created_at"


def now() -> datetime:
    return datetime.now(timezone.utc)


def toggle(db, user: dict, listing_id: str) -> dict:
    listing = get_listing_row(db, listing_id)
    if listing is None:
        raise NotFound("listing not found")
    existing = fetch_one(db, f"SELECT {FAV_COLS} FROM favorites WHERE user_id = %s AND listing_id = %s", (user["_id"], listing_id))
    if existing:
        execute(db, "DELETE FROM favorites WHERE id = %s", (existing["_id"],))
        return {"favorited": False}
    execute(
        db,
        "INSERT INTO favorites (user_id, listing_id, created_at) VALUES (%s, %s, %s)",
        (user["_id"], listing_id, now()),
    )
    return {"favorited": True}


def list_favorites(db, user: dict, page: int = 1, page_size: int = 20) -> dict:
    total = fetch_one(db, "SELECT count(*) AS n FROM favorites WHERE user_id = %s", (user["_id"],))["n"]
    rows = fetch_all(
        db,
        f"SELECT {FAV_COLS} FROM favorites WHERE user_id = %s ORDER BY created_at DESC LIMIT %s OFFSET %s",
        (user["_id"], page_size, (page - 1) * page_size),
    )
    items = []
    for fav in rows:
        listing = fetch_one(db, f"SELECT {LISTING_COLS} FROM listings WHERE id = %s", (fav["listing"],))
        if listing is None or listing.get("status") == "deleted":
            continue
        items.append(
            {
                "id": str(fav["_id"]),
                "listing": listing_snapshot(db, listing),
                "created_at": fav.get("created_at").isoformat() if fav.get("created_at") else None,
            }
        )
    return {"items": items, "total": total, "page": page, "page_size": page_size, "pages": max((total + page_size - 1) // page_size, 1)}
