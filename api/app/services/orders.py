"""Orders domain — buyer→seller order requests with a status state machine.

    placed ──accept──▶ accepted ──fulfill──▶ fulfilled ──complete──▶ completed
       │                   │
     reject              cancel
       ▼                   ▼
   rejected            cancelled

Role rules: seller may ``accept`` / ``reject`` / ``fulfill``; buyer may ``cancel``;
either party may ``complete`` once ``fulfilled``.
"""

from __future__ import annotations

from datetime import datetime, timezone

from bson import ObjectId
from pymongo import DESCENDING

from shared.errors import Forbidden, NotFound, ValidationError
from shared.mongo import COLLECTIONS
from shared.roles import Role

from .notifications import notify
from .serializers import order_public

# (from_status, action) -> to_status
TRANSITIONS: dict[tuple[str, str], str] = {
    ("placed", "accept"): "accepted",
    ("placed", "reject"): "rejected",
    ("placed", "cancel"): "cancelled",
    ("accepted", "fulfill"): "fulfilled",
    ("accepted", "cancel"): "cancelled",
    ("fulfilled", "complete"): "completed",
}

# who is allowed to perform each action
ACTION_ACTOR = {
    "accept": "seller",
    "reject": "seller",
    "fulfill": "seller",
    "cancel": "buyer",
    "complete": "buyer",
}

NOTIFY_TYPE = {
    "accept": "order.accepted",
    "reject": "order.rejected",
    "fulfill": "order.fulfilled",
    "complete": "order.completed",
    "cancel": "order.cancelled",
}


def now() -> datetime:
    return datetime.now(timezone.utc)


def insert_order(
    db,
    listing: dict,
    buyer_id: ObjectId,
    seller_id: ObjectId,
    quantity: float,
    unit_price: float,
    note: str = "",
) -> dict:
    """Low-level insert used by both ``create`` and the bid-accept flow."""
    doc = {
        "listing": listing["_id"],
        "buyer": buyer_id,
        "seller": seller_id,
        "quantity": float(quantity),
        "unit_price": round(float(unit_price), 2),
        "total": round(float(quantity) * float(unit_price), 2),
        "note": note,
        "status": "placed",
        "history": [{"status": "placed", "at": now().isoformat(), "by": str(buyer_id)}],
        "created_at": now(),
        "updated_at": now(),
    }
    result = db[COLLECTIONS["orders"]].insert_one(doc)
    doc["_id"] = result.inserted_id
    notify(db, str(seller_id), "order.new", {"order_id": str(doc["_id"]), "listing_id": str(listing["_id"])})
    return order_public(db, doc)


def create(db, user: dict, listing_id: str, quantity: float, note: str = "") -> dict:
    try:
        listing = db[COLLECTIONS["listings"]].find_one({"_id": ObjectId(listing_id)})
    except Exception as exc:
        raise NotFound("listing not found") from exc
    if listing is None or listing.get("status") == "deleted":
        raise NotFound("listing not found")
    if listing.get("status") not in ("active", "sold"):
        raise ValidationError("listing is not orderable")
    if listing.get("seller") == user["_id"]:
        raise ValidationError("cannot order your own listing")

    return insert_order(
        db,
        listing=listing,
        buyer_id=user["_id"],
        seller_id=listing["seller"],
        quantity=quantity,
        unit_price=listing.get("price", 0),
        note=note or "",
    )


def list_orders(db, user: dict, side: str = "buying", status: str = "", page: int = 1, page_size: int = 20) -> dict:
    query: dict = {"buyer" if side == "buying" else "seller": user["_id"]}
    if status:
        query["status"] = status
    coll = db[COLLECTIONS["orders"]]
    total = coll.count_documents(query)
    cursor = coll.find(query).sort("created_at", DESCENDING).skip((page - 1) * page_size).limit(page_size)
    items = [order_public(db, o) for o in cursor]
    return {"items": items, "total": total, "page": page, "page_size": page_size, "pages": max((total + page_size - 1) // page_size, 1)}


def get(db, user: dict, order_id: str) -> dict:
    order = _get(db, order_id)
    if user["_id"] not in (order.get("buyer"), order.get("seller")) and user.get("role") not in (
        Role.ADMIN,
        Role.MODERATOR,
    ):
        raise Forbidden("you are not part of this order")
    return order_public(db, order)


def transition(db, user: dict, order_id: str, action: str) -> dict:
    order = _get(db, order_id)
    current = order.get("status")

    key = (current, action)
    if key not in TRANSITIONS:
        raise ValidationError(f"cannot '{action}' an order that is '{current}'")

    actor = ACTION_ACTOR[action]
    is_staff = user.get("role") in (Role.ADMIN, Role.MODERATOR)
    if not is_staff:
        if actor == "seller" and order.get("seller") != user["_id"]:
            raise Forbidden("only the seller can perform this action")
        if actor == "buyer" and order.get("buyer") != user["_id"]:
            raise Forbidden("only the buyer can perform this action")

    new_status = TRANSITIONS[key]
    db[COLLECTIONS["orders"]].update_one(
        {"_id": order["_id"]},
        {
            "$set": {"status": new_status, "updated_at": now()},
            "$push": {"history": {"status": new_status, "at": now().isoformat(), "by": str(user["_id"])}},
        },
    )
    counterparty = order["seller"] if user["_id"] == order["buyer"] else order["buyer"]
    notify(
        db,
        str(counterparty),
        NOTIFY_TYPE[action],
        {"order_id": str(order["_id"]), "status": new_status},
    )
    return order_public(db, db[COLLECTIONS["orders"]].find_one({"_id": order["_id"]}))


def _get(db, order_id: str) -> dict:
    try:
        order = db[COLLECTIONS["orders"]].find_one({"_id": ObjectId(order_id)})
    except Exception as exc:
        raise NotFound("order not found") from exc
    if order is None:
        raise NotFound("order not found")
    return order