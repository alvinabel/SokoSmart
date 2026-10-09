"""Categories domain — read is public, write is moderator/admin."""

from __future__ import annotations

from datetime import datetime, timezone

from shared.errors import Conflict, NotFound
from shared.mongo import COLLECTIONS


def now() -> datetime:
    return datetime.now(timezone.utc)


def list_categories(db) -> list[dict]:
    return [
        {
            "slug": c["slug"],
            "name": c.get("name", c["slug"]),
            "emoji": c.get("emoji", "🥬"),
            "color": c.get("color", "#4CAF50"),
        }
        for c in db[COLLECTIONS["categories"]].find().sort("name", 1)
    ]


def create(db, data: dict) -> dict:
    if db[COLLECTIONS["categories"]].find_one({"slug": data["slug"]}):
        raise Conflict("category slug already exists")
    doc = {**data, "created_at": now()}
    db[COLLECTIONS["categories"]].insert_one(doc)
    return {k: doc.get(k) for k in ("slug", "name", "emoji", "color")}


def update(db, slug: str, data: dict) -> dict:
    doc = db[COLLECTIONS["categories"]].find_one({"slug": slug})
    if doc is None:
        raise NotFound("category not found")
    payload = {**{k: v for k, v in data.items() if v is not None}, "updated_at": now()}
    db[COLLECTIONS["categories"]].update_one({"slug": slug}, {"$set": payload})
    merged = {**doc, **payload}
    return {k: merged.get(k) for k in ("slug", "name", "emoji", "color")}


def delete(db, slug: str) -> None:
    if db[COLLECTIONS["categories"]].find_one({"slug": slug}) is None:
        raise NotFound("category not found")
    db[COLLECTIONS["categories"]].delete_one({"slug": slug})