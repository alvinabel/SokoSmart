"""Notifications domain — server-generated event feed per recipient."""

from __future__ import annotations

from datetime import datetime, timezone

from bson import ObjectId
from pymongo import DESCENDING

from shared.errors import NotFound
from shared.mongo import COLLECTIONS

VALID_TYPES = {
    "order.new",
    "order.accepted",
    "order.rejected",
    "order.fulfilled",
    "order.completed",
    "order.cancelled",
    "bid.new",
    "bid.accepted",
    "bid.declined",
    "message.new",
    "review.new",
    "listing.moderated",
}


def now() -> datetime:
    return datetime.now(timezone.utc)


def notify(db, recipient_id: str, type_: str, data: dict | None = None) -> None:
    """Insert a notification. Silently ignores self-notifications."""
    if not recipient_id:
        return
    try:
        recipient = ObjectId(recipient_id)
    except Exception:
        return
    db[COLLECTIONS["notifications"]].insert_one(
        {
            "recipient": recipient,
            "type": type_ if type_ in VALID_TYPES else "system",
            "read": False,
            "data": data or {},
            "created_at": now(),
        }
    )


def _public(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "type": doc.get("type", "system"),
        "read": doc.get("read", False),
        "data": doc.get("data", {}),
        "created_at": doc.get("created_at").isoformat() if doc.get("created_at") else None,
    }


def list_notifications(db, user: dict, unread_only: bool = False, page: int = 1, page_size: int = 20) -> dict:
    query: dict = {"recipient": user["_id"]}
    if unread_only:
        query["read"] = False
    coll = db[COLLECTIONS["notifications"]]
    total = coll.count_documents(query)
    cursor = coll.find(query).sort("created_at", DESCENDING).skip((page - 1) * page_size).limit(page_size)
    items = [_public(d) for d in cursor]
    return {"items": items, "total": total, "page": page, "page_size": page_size, "pages": max((total + page_size - 1) // page_size, 1)}


def unread_count(db, user: dict) -> int:
    return db[COLLECTIONS["notifications"]].count_documents({"recipient": user["_id"], "read": False})


def mark_read(db, user: dict, notification_id: str) -> dict:
    try:
        oid = ObjectId(notification_id)
    except Exception as exc:
        raise NotFound("notification not found") from exc
    result = db[COLLECTIONS["notifications"]].update_one(
        {"_id": oid, "recipient": user["_id"]}, {"$set": {"read": True}}
    )
    if result.matched_count == 0:
        raise NotFound("notification not found")
    return {"id": notification_id, "read": True}


def mark_all_read(db, user: dict) -> dict:
    result = db[COLLECTIONS["notifications"]].update_many(
        {"recipient": user["_id"], "read": False}, {"$set": {"read": True}}
    )
    return {"updated": result.modified_count}


def clear_read(db, user: dict) -> None:
    db[COLLECTIONS["notifications"]].delete_many({"recipient": user["_id"], "read": True})