"""Serialization helpers shared by every service.

Always return JSON-safe primitives (str ids, plain dicts, ISO timestamps).
"""

from __future__ import annotations

from bson import ObjectId
from pymongo import DESCENDING

from shared.mongo import COLLECTIONS


def public_id(value: ObjectId) -> str:
    return str(value)


def iso(value) -> str | None:
    return value.isoformat() if value else None


def user_summary(user: dict | None) -> dict:
    """A buyer-visible view of a user (no email/password)."""
    if not user:
        return {}
    rating = user.get("rating") or {"avg": 0, "count": 0}
    return {
        "id": public_id(user["_id"]),
        "name": user.get("name", ""),
        "role": user.get("role", "buyer"),
        "phone": user.get("phone", ""),
        "location": user.get("location") or {},
        "rating": rating,
        "verified": user.get("verified", False),
        "created_at": iso(user.get("created_at")),
    }


def category_meta(db, slug: str) -> dict:
    cat = db[COLLECTIONS["categories"]].find_one({"slug": slug})
    return {
        "slug": slug,
        "name": cat["name"] if cat else slug.title(),
        "emoji": cat.get("emoji", "🥬") if cat else "🥬",
        "color": cat.get("color", "#4CAF50") if cat else "#4CAF50",
    }


def listing_public(db, listing: dict) -> dict:
    """Full listing shape for detail & list views (joins seller + category)."""
    cat = category_meta(db, listing.get("category", ""))
    seller = db[COLLECTIONS["users"]].find_one({"_id": listing.get("seller")})
    return {
        "id": public_id(listing["_id"]),
        "title": listing.get("title", ""),
        "description": listing.get("description", ""),
        "category": listing.get("category", ""),
        "category_meta": cat,
        "price": listing.get("price", 0),
        "unit": listing.get("unit", "unit"),
        "quantity": listing.get("quantity", 1),
        "quality": listing.get("quality"),
        "location": listing.get("location") or {},
        "images": listing.get("images", []),
        "status": listing.get("status", "active"),
        "views": listing.get("views", 0),
        "seller": user_summary(seller),
        "created_at": iso(listing.get("created_at")),
    }


def listing_snapshot(db, listing: dict | None) -> dict | None:
    """Compact listing reference used in orders/bids/favorites lists."""
    if not listing:
        return None
    return {
        "id": public_id(listing["_id"]),
        "title": listing.get("title", ""),
        "price": listing.get("price", 0),
        "unit": listing.get("unit", "unit"),
        "category_meta": category_meta(db, listing.get("category", "")),
        "status": listing.get("status", "active"),
    }


def order_public(db, order: dict) -> dict:
    buyer = db[COLLECTIONS["users"]].find_one({"_id": order.get("buyer")})
    seller = db[COLLECTIONS["users"]].find_one({"_id": order.get("seller")})
    listing = db[COLLECTIONS["listings"]].find_one({"_id": order.get("listing")})
    return {
        "id": public_id(order["_id"]),
        "status": order.get("status"),
        "quantity": order.get("quantity", 1),
        "unit_price": order.get("unit_price", 0),
        "total": order.get("total", 0),
        "note": order.get("note", ""),
        "listing": listing_snapshot(db, listing),
        "buyer": user_summary(buyer),
        "seller": user_summary(seller),
        "history": order.get("history", []),
        "created_at": iso(order.get("created_at")),
        "updated_at": iso(order.get("updated_at")),
    }


def newest(field: str = "created_at"):
    return [(field, DESCENDING)]