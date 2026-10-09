"""Messages domain — 1:1 chat keyed by a deterministic conversation id.

Conversation id = the two user ids sorted and joined with ``:`` so both parties
derive the same key. v1 uses REST + client polling; swap in WebSockets/SSE later
without changing the storage shape.
"""

from __future__ import annotations

from datetime import datetime, timezone

from bson import ObjectId
from pymongo import DESCENDING

from shared.errors import NotFound, ValidationError
from shared.mongo import COLLECTIONS

from .notifications import notify
from .serializers import user_summary


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
    try:
        user = db[COLLECTIONS["users"]].find_one({"_id": ObjectId(user_id)})
    except Exception as exc:
        raise NotFound("user not found") from exc
    if user is None:
        raise NotFound("user not found")
    return user


def send(db, user: dict, recipient_id: str, body: str, listing_id: str | None = None) -> dict:
    recipient = _get_user(db, recipient_id)
    if recipient["_id"] == user["_id"]:
        raise ValidationError("cannot message yourself")

    doc = {
        "conversation": conversation_id(user["_id"], recipient["_id"]),
        "sender": user["_id"],
        "recipient": recipient["_id"],
        "body": body.strip(),
        "listing_id": ObjectId(listing_id) if listing_id else None,
        "read": False,
        "created_at": now(),
    }
    result = db[COLLECTIONS["messages"]].insert_one(doc)
    doc["_id"] = result.inserted_id
    notify(db, str(recipient["_id"]), "message.new", {"from": str(user["_id"])})
    return _public(doc)


def thread(db, user: dict, other_id: str, page: int = 1, page_size: int = 50) -> dict:
    other = _get_user(db, other_id)
    conv = conversation_id(user["_id"], other["_id"])
    coll = db[COLLECTIONS["messages"]]
    query = {"conversation": conv}
    total = coll.count_documents(query)

    coll.update_many(
        {"conversation": conv, "recipient": user["_id"], "read": False}, {"$set": {"read": True}}
    )

    cursor = coll.find(query).sort("created_at", DESCENDING).skip((page - 1) * page_size).limit(page_size)
    items = [_public(m) for m in reversed(list(cursor))]
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
    coll = db[COLLECTIONS["messages"]]
    query = {"$or": [{"sender": user["_id"]}, {"recipient": user["_id"]}]}
    messages = list(coll.find(query).sort("created_at", DESCENDING).limit(limit))

    conversations: dict[str, dict] = {}
    unread: dict[str, int] = {}
    for msg in messages:
        conv = msg["conversation"]
        other_id = msg["recipient"] if msg["sender"] == user["_id"] else msg["sender"]
        key = str(other_id)
        if key not in conversations:
            other = db[COLLECTIONS["users"]].find_one({"_id": other_id})
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