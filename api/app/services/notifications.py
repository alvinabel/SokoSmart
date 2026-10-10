"""Notifications domain — server-generated event feed per recipient."""

from __future__ import annotations

from datetime import datetime, timezone

from psycopg.types.json import Json

from shared.db import execute, fetch_all, fetch_one, insert_returning
from shared.errors import NotFound

NOTIF_COLS = "id AS _id, recipient_id AS recipient, type, read, data, created_at"

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
    """Insert a notification. Silently ignores missing recipients."""
    if not recipient_id:
        return
    insert_returning(
        db,
        "INSERT INTO notifications (recipient_id, type, read, data, created_at) "
        "VALUES (%s, %s, false, %s, %s) RETURNING id",
        (recipient_id, type_ if type_ in VALID_TYPES else "system", Json(data or {}), now()),
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
    where = ["recipient_id = %s"]
    params: list = [user["_id"]]
    if unread_only:
        where.append("read = false")
    clause = " AND ".join(where)
    total = fetch_one(db, f"SELECT count(*) AS n FROM notifications WHERE {clause}", tuple(params))["n"]
    rows = fetch_all(
        db,
        f"SELECT {NOTIF_COLS} FROM notifications WHERE {clause} ORDER BY created_at DESC LIMIT %s OFFSET %s",
        tuple(params) + (page_size, (page - 1) * page_size),
    )
    items = [_public(d) for d in rows]
    return {"items": items, "total": total, "page": page, "page_size": page_size, "pages": max((total + page_size - 1) // page_size, 1)}


def unread_count(db, user: dict) -> int:
    return fetch_one(
        db, "SELECT count(*) AS n FROM notifications WHERE recipient_id = %s AND read = false", (user["_id"],)
    )["n"]


def mark_read(db, user: dict, notification_id: str) -> dict:
    row = fetch_one(
        db,
        "UPDATE notifications SET read = true WHERE id = %s AND recipient_id = %s RETURNING id AS _id",
        (notification_id, user["_id"]),
    )
    if row is None:
        raise NotFound("notification not found")
    return {"id": notification_id, "read": True}


def mark_all_read(db, user: dict) -> dict:
    updated = execute(
        db, "UPDATE notifications SET read = true WHERE recipient_id = %s AND read = false", (user["_id"],)
    )
    return {"updated": updated}


def clear_read(db, user: dict) -> None:
    execute(db, "DELETE FROM notifications WHERE recipient_id = %s AND read = true", (user["_id"],))
