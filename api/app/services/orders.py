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

from psycopg.types.json import Json

from shared.db import fetch_all, fetch_one, insert_returning
from shared.errors import Forbidden, NotFound, ValidationError
from shared.roles import Role

from .notifications import notify
from .serializers import ORDER_COLS, get_listing_row, order_public

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


def insert_order(db, listing: dict, buyer_id: str, seller_id: str, quantity: float, unit_price: float, note: str = "") -> dict:
    history = [{"status": "placed", "at": now().isoformat(), "by": str(buyer_id)}]
    row = insert_returning(
        db,
        f"""
        INSERT INTO orders
            (listing_id, buyer_id, seller_id, quantity, unit_price, total, note,
             status, history, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, 'placed', %s, %s, %s)
        RETURNING {ORDER_COLS}
        """,
        (
            listing["_id"],
            buyer_id,
            seller_id,
            float(quantity),
            float(unit_price),
            round(float(quantity) * float(unit_price), 2),
            note,
            Json(history),
            now(),
            now(),
        ),
    )
    notify(db, str(seller_id), "order.new", {"order_id": str(row["_id"]), "listing_id": str(listing["_id"])})
    return order_public(db, row)


def create(db, user: dict, listing_id: str, quantity: float, note: str = "") -> dict:
    listing = get_listing_row(db, listing_id)
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
    column = "buyer_id" if side == "buying" else "seller_id"
    where = [f"{column} = %s"]
    params: list = [user["_id"]]
    if status:
        where.append("status = %s")
        params.append(status)
    clause = " AND ".join(where)

    total = fetch_one(db, f"SELECT count(*) AS n FROM orders WHERE {clause}", tuple(params))["n"]
    rows = fetch_all(
        db,
        f"SELECT {ORDER_COLS} FROM orders WHERE {clause} ORDER BY created_at DESC LIMIT %s OFFSET %s",
        tuple(params) + (page_size, (page - 1) * page_size),
    )
    items = [order_public(db, o) for o in rows]
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
    entry = Json([{"status": new_status, "at": now().isoformat(), "by": str(user["_id"])}])
    row = fetch_one(
        db,
        f"""
        UPDATE orders
        SET status = %s, updated_at = %s, history = history || %s::jsonb
        WHERE id = %s
        RETURNING {ORDER_COLS}
        """,
        (new_status, now(), entry, order["_id"]),
    )
    counterparty = order["seller"] if user["_id"] == order["buyer"] else order["buyer"]
    notify(
        db,
        str(counterparty),
        NOTIFY_TYPE[action],
        {"order_id": str(order["_id"]), "status": new_status},
    )
    return order_public(db, row)


def _get(db, order_id: str) -> dict:
    order = fetch_one(db, f"SELECT {ORDER_COLS} FROM orders WHERE id = %s", (order_id,))
    if order is None:
        raise NotFound("order not found")
    return order
