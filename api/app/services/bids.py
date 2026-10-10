"""Bids domain — price negotiation between buyer and seller.

Accepting a bid automatically:
  - declines all other pending bids on the listing,
  - creates a ``placed`` order at the bid amount,
  - marks the listing ``sold``.
"""

from __future__ import annotations

from datetime import datetime, timezone

from shared.db import execute, fetch_all, fetch_one, insert_returning
from shared.errors import Forbidden, NotFound, ValidationError
from shared.roles import Role

from .notifications import notify
from .orders import insert_order
from .serializers import get_listing_row

BID_COLS = "id AS _id, listing_id AS listing, bidder_id AS bidder, amount, status, created_at, updated_at, accepted_at"


def now() -> datetime:
    return datetime.now(timezone.utc)


def _bid_public(db, bid: dict) -> dict:
    listing = get_listing_row(db, bid.get("listing"))
    return {
        "id": str(bid["_id"]),
        "listing_id": str(bid.get("listing")),
        "listing_title": listing.get("title") if listing else None,
        "amount": bid.get("amount", 0),
        "status": bid.get("status", "pending"),
        "created_at": bid.get("created_at").isoformat() if bid.get("created_at") else None,
    }


def create(db, user: dict, listing_id: str, amount: float) -> dict:
    listing = get_listing_row(db, listing_id)
    if listing is None or listing.get("status") == "deleted":
        raise NotFound("listing not found")
    if listing.get("status") != "active":
        raise ValidationError("listing is not open for bids")
    if listing.get("seller") == user["_id"]:
        raise ValidationError("cannot bid on your own listing")

    row = insert_returning(
        db,
        f"""
        INSERT INTO bids (listing_id, bidder_id, amount, status, created_at)
        VALUES (%s, %s, %s, 'pending', %s)
        RETURNING {BID_COLS}
        """,
        (listing["_id"], user["_id"], round(float(amount), 2), now()),
    )
    notify(db, str(listing.get("seller")), "bid.new", {"listing_id": listing_id, "amount": row["amount"]})
    return _bid_public(db, row)


def list_mine(db, user: dict, page: int = 1, page_size: int = 20) -> dict:
    total = fetch_one(db, "SELECT count(*) AS n FROM bids WHERE bidder_id = %s", (user["_id"],))["n"]
    rows = fetch_all(
        db,
        f"SELECT {BID_COLS} FROM bids WHERE bidder_id = %s ORDER BY created_at DESC LIMIT %s OFFSET %s",
        (user["_id"], page_size, (page - 1) * page_size),
    )
    items = [_bid_public(db, b) for b in rows]
    return {"items": items, "total": total, "page": page, "page_size": page_size, "pages": max((total + page_size - 1) // page_size, 1)}


def list_for_listing(db, user: dict, listing_id: str) -> list[dict]:
    listing = get_listing_row(db, listing_id)
    if listing is None:
        raise NotFound("listing not found")
    role = user.get("role")
    if listing.get("seller") != user["_id"] and role not in (Role.ADMIN, Role.MODERATOR):
        raise Forbidden("only the listing owner may view bids")
    rows = fetch_all(
        db,
        f"SELECT {BID_COLS} FROM bids WHERE listing_id = %s ORDER BY amount DESC",
        (listing["_id"],),
    )
    return [_bid_public(db, b) for b in rows]


def respond(db, user: dict, bid_id: str, action: str) -> dict:
    bid = fetch_one(db, f"SELECT {BID_COLS} FROM bids WHERE id = %s", (bid_id,))
    if bid is None:
        raise NotFound("bid not found")
    listing = get_listing_row(db, bid.get("listing"))
    if listing is None:
        raise NotFound("listing not found")
    role = user.get("role")
    if listing.get("seller") != user["_id"] and role not in (Role.ADMIN, Role.MODERATOR):
        raise Forbidden("only the listing owner may respond to bids")
    if bid.get("status") != "pending":
        raise ValidationError("bid is no longer pending")

    if action == "decline":
        row = fetch_one(
            db,
            f"UPDATE bids SET status = 'declined', updated_at = %s WHERE id = %s RETURNING {BID_COLS}",
            (now(), bid["_id"]),
        )
        return _bid_public(db, row)

    # accept:
    execute(
        db,
        "UPDATE bids SET status = 'declined', updated_at = %s WHERE listing_id = %s AND status = 'pending'",
        (now(), bid["listing"]),
    )
    fetch_one(
        db,
        f"UPDATE bids SET status = 'accepted', accepted_at = %s WHERE id = %s RETURNING {BID_COLS}",
        (now(), bid["_id"]),
    )
    fetch_one(
        db,
        "UPDATE listings SET status = 'sold', sold_price = %s, updated_at = %s WHERE id = %s RETURNING id",
        (bid["amount"], now(), listing["_id"]),
    )
    insert_order(
        db,
        listing=listing,
        buyer_id=bid["bidder"],
        seller_id=listing["seller"],
        quantity=1,
        unit_price=bid["amount"],
        note=f"Accepted bid of {bid['amount']}",
    )
    notify(db, str(bid.get("bidder")), "bid.accepted", {"listing_id": str(listing["_id"]), "amount": bid["amount"]})
    row = fetch_one(db, f"SELECT {BID_COLS} FROM bids WHERE id = %s", (bid["_id"],))
    return _bid_public(db, row)
