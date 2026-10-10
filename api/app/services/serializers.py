"""Serialization helpers shared by every service.

Always return JSON-safe primitives (str ids, plain dicts, ISO timestamps).

Rows are fetched with columns aliased back to the original document field names
(``id AS _id``, ``seller_id AS seller``, ...) so these helpers stay stable.
"""

from __future__ import annotations

from shared.db import fetch_one

USER_COLS = "id AS _id, name, email, role, phone, bio, location, status, verified, rating, created_at"
LISTING_COLS = (
    "id AS _id, title, description, category, price, unit, quantity, quality, "
    "location, images, seller_id AS seller, status, views, sold_price, created_at, updated_at"
)
ORDER_COLS = (
    "id AS _id, listing_id AS listing, buyer_id AS buyer, seller_id AS seller, "
    "quantity, unit_price, total, note, status, history, created_at, updated_at"
)


def get_user(db, user_id) -> dict | None:
    if not user_id:
        return None
    return fetch_one(db, f"SELECT {USER_COLS} FROM users WHERE id = %s", (user_id,))


def get_listing_row(db, listing_id) -> dict | None:
    if not listing_id:
        return None
    return fetch_one(db, f"SELECT {LISTING_COLS} FROM listings WHERE id = %s", (listing_id,))


def get_order_row(db, order_id) -> dict | None:
    if not order_id:
        return None
    return fetch_one(db, f"SELECT {ORDER_COLS} FROM orders WHERE id = %s", (order_id,))


def public_id(value) -> str:
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
    cat = fetch_one(db, "SELECT slug, name, emoji, color FROM categories WHERE slug = %s", (slug,))
    return {
        "slug": slug,
        "name": cat["name"] if cat else slug.title(),
        "emoji": cat.get("emoji", "🥬") if cat else "🥬",
        "color": cat.get("color", "#4CAF50") if cat else "#4CAF50",
    }


def listing_public(db, listing: dict) -> dict:
    """Full listing shape for detail & list views (joins seller + category)."""
    cat = category_meta(db, listing.get("category", ""))
    seller = get_user(db, listing.get("seller"))
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
    buyer = get_user(db, order.get("buyer"))
    seller = get_user(db, order.get("seller"))
    listing = get_listing_row(db, order.get("listing"))
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
    """Backwards-compatible sort helper (descending)."""
    return [(field, -1)]
