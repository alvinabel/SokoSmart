"""Messages domain — 1:1 chat keyed by a deterministic conversation id.

Conversation id = the two user ids sorted and joined with ``:`` so both parties
derive the same key. v1 uses REST + client polling; swap in WebSockets/SSE later
without changing the storage shape.
"""

from __future__ import annotations

from datetime import datetime, timezone

from shared.db import execute, fetch_all, fetch_one, insert_returning
from shared.errors import NotFound, ValidationError

from .notifications import notify
from .serializers import get_user, user_summary

MSG_COLS = (
    "id AS _id, conversation, sender_id AS sender, recipient_id AS recipient, "
    "body, listing_id, read, created_at"
)


def now() -> datetime:
    return datetime.now(timezone.utc)


def conversation_id(a: str, b: str) -> str:
    return ":".join(sorted([str(a), str(b)]))


def _public(msg: dict) -> dict:
    return {
        "id": str(msg["_id"]),
        "sender": str(msg.get("sender")),
        "recipient": str(msg.get("recipient")),
        "body": msg.get("body", ""),
        "listing_id": str(msg["listing_id"]) if msg.get("listing_id") else None,
        "read": msg.get("read", False),
        "created_at": msg.get("created_at").isoformat() if msg.get("created_at") else None,
    }


def _get_user(db, user_id: str) -> dict:
    user = get_user(db, user_id)
    if user is None:
        raise NotFound("user not found")
    return user


def send(db, user: dict, recipient_id: str, body: str, listing_id: str | None = None) -> dict:
    recipient = _get_user(db, recipient_id)
    if recipient["_id"] == user["_id"]:
        raise ValidationError("cannot message yourself")

    row = insert_returning(
        db,
        f"""
        INSERT INTO messages (conversation, sender_id, recipient_id, body, listing_id, read, created_at)
        VALUES (%s, %s, %s, %s, %s, false, %s)
        RETURNING {MSG_COLS}
        """,
        (conversation_id(user["_id"], recipient["_id"]), user["_id"], recipient["_id"], body.strip(), listing_id, now()),
    )
    notify(db, str(recipient["_id"]), "message.new", {"from": str(user["_id"])})
    return _public(row)


def thread(db, user: dict, other_id: str, page: int = 1, page_size: int = 50) -> dict:
    other = _get_user(db, other_id)
    conv = conversation_id(user["_id"], other["_id"])
    total = fetch_one(db, "SELECT count(*) AS n FROM messages WHERE conversation = %s", (conv,))["n"]

    execute(
        db,
        "UPDATE messages SET read = true WHERE conversation = %s AND recipient_id = %s AND read = false",
        (conv, user["_id"]),
    )

    rows = fetch_all(
        db,
        f"SELECT {MSG_COLS} FROM messages WHERE conversation = %s ORDER BY created_at DESC LIMIT %s OFFSET %s",
        (conv, page_size, (page - 1) * page_size),
    )
    items = [_public(m) for m in reversed(rows)]
    return {
        "conversation_id": conv,
        "with": user_summary(other),
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": max((total + page_size - 1) // page_size, 1),
    }


def inbox(db, user: dict, limit: int = 500) -> dict:
    """Latest message per counterparty + unread count (computed in Python for MVP scale)."""
    rows = fetch_all(
        db,
        f"SELECT {MSG_COLS} FROM messages WHERE sender_id = %s OR recipient_id = %s "
        "ORDER BY created_at DESC LIMIT %s",
        (user["_id"], user["_id"], limit),
    )

    conversations: dict[str, dict] = {}
    for msg in rows:
        other_id = msg["recipient"] if msg["sender"] == user["_id"] else msg["sender"]
        key = str(other_id)
        if key not in conversations:
            other = get_user(db, other_id)
            conversations[key] = {
                "with": user_summary(other),
                "last_message": msg.get("body", ""),
                "last_at": msg.get("created_at").isoformat() if msg.get("created_at") else None,
                "listing_id": str(msg["listing_id"]) if msg.get("listing_id") else None,
                "unread": 0,
            }
        if msg["recipient"] == user["_id"] and not msg.get("read"):
            conversations[key]["unread"] += 1

    ordered = sorted(conversations.values(), key=lambda c: c["last_at"] or "", reverse=True)
    return {"items": ordered, "total": len(ordered)}
