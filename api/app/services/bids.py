"""Bids domain — price negotiation between buyer and seller.

Accepting a bid automatically:
  - declines all other pending bids on the listing,
  - creates a ``placed`` order at the bid amount,
  - marks the listing ``sold``.
"""

from __future__ import annotations

from datetime import datetime, timezone

from bson import ObjectId
from pymongo import DESCENDING

from shared.errors import Forbidden, NotFound, ValidationError
from shared.mongo import COLLECTIONS
from shared.roles import Role

from .notifications import notify
from .orders import insert_order


def now() -> datetime:
    return datetime.now(timezone.utc)


def _bid_public(db, bid: dict) -> dict:
    listing = db[COLLECTIONS["listings"]].find_one({"_id": bid.get("listing")})
    return {
        "id": str(bid["_id"]),
        "listing_id": str(bid.get("listing")),
        "listing_title": listing.get("title") if listing else None,
        "amount": bid.get("amount", 0),
        "status": bid.get("status", "pending"),
        "created_at": bid.get("created_at").isoformat() if bid.get("created_at") else None,
    }


def create(db, user: dict, listing_id: str, amount: float) -> dict:
    try:
        listing = db[COLLECTIONS["listings"]].find_one({"_id": ObjectId(listing_id)})
    except Exception as exc:
        raise NotFound("listing not found") from exc
    if listing is None or listing.get("status") == "deleted":
        raise NotFound("listing not found")
    if listing.get("status") != "active":
        raise ValidationError("listing is not open for bids")
    if listing.get("seller") == user["_id"]:
        raise ValidationError("cannot bid on your own listing")

    doc = {
        "listing": listing["_id"],
        "bidder": user["_id"],
        "amount": round(float(amount), 2),
        "status": "pending",
        "created_at": now(),
    }
    result = db[COLLECTIONS["bids"]].insert_one(doc)
    doc["_id"] = result.inserted_id
    notify(db, str(listing.get("seller")), "bid.new", {"listing_id": listing_id, "amount": doc["amount"]})
    return _bid_public(db, doc)


def list_mine(db, user: dict, page: int = 1, page_size: int = 20) -> dict:
    coll = db[COLLECTIONS["bids"]]
    query = {"bidder": user["_id"]}
    total = coll.count_documents(query)
    cursor = coll.find(query).sort("created_at", DESCENDING).skip((page - 1) * page_size).limit(page_size)
    items = [_bid_public(db, b) for b in cursor]
    return {"items": items, "total": total, "page": page, "page_size": page_size, "pages": max((total + page_size - 1) // page_size, 1)}


def list_for_listing(db, user: dict, listing_id: str) -> list[dict]:
    listing = db[COLLECTIONS["listings"]].find_one({"_id": _oid(listing_id)})
    if listing is None:
        raise NotFound("listing not found")
    role = user.get("role")
    if listing.get("seller") != user["_id"] and role not in (Role.ADMIN, Role.MODERATOR):
        raise Forbidden("only the listing owner may view bids")
    bids = db[COLLECTIONS["bids"]].find({"listing": listing["_id"]}).sort("amount", DESCENDING)
    return [_bid_public(db, b) for b in bids]


def respond(db, user: dict, bid_id: str, action: str) -> dict:
    bid = db[COLLECTIONS["bids"]].find_one({"_id": _oid(bid_id)})
    if bid is None:
        raise NotFound("bid not found")
    listing = db[COLLECTIONS["listings"]].find_one({"_id": bid.get("listing")})
    if listing is None:
        raise NotFound("listing not found")
    role = user.get("role")
    if listing.get("seller") != user["_id"] and role not in (Role.ADMIN, Role.MODERATOR):
        raise Forbidden("only the listing owner may respond to bids")
    if bid.get("status") != "pending":
        raise ValidationError("bid is no longer pending")

    if action == "decline":
        db[COLLECTIONS["bids"]].update_one({"_id": bid["_id"]}, {"$set": {"status": "declined", "updated_at": now()}})
        return _bid_public(db, db[COLLECTIONS["bids"]].find_one({"_id": bid["_id"]}))

    # accept:
    db[COLLECTIONS["bids"]].update_many(
        {"listing": bid["listing"], "status": "pending"},
        {"$set": {"status": "declined", "updated_at": now()}},
    )
    db[COLLECTIONS["bids"]].update_one(
        {"_id": bid["_id"]}, {"$set": {"status": "accepted", "accepted_at": now()}}
    )
    db[COLLECTIONS["listings"]].update_one(
        {"_id": listing["_id"]}, {"$set": {"status": "sold", "sold_price": bid["amount"], "updated_at": now()}}
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
    return _bid_public(db, db[COLLECTIONS["bids"]].find_one({"_id": bid["_id"]}))


def _oid(bid_id: str) -> ObjectId:
    try:
        return ObjectId(bid_id)
    except Exception as exc:
        raise NotFound("bid not found") from exc