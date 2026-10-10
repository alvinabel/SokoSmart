"""Listings domain — CRUD, search/filter, view counting, ownership rules."""

from __future__ import annotations

from datetime import datetime, timezone

from psycopg.types.json import Json

from shared.db import fetch_all, fetch_one, insert_returning
from shared.errors import Forbidden, NotFound, ValidationError
from shared.roles import Role

from .serializers import LISTING_COLS, listing_public

SORT_MAP = {
    "newest": "created_at DESC",
    "price_asc": "price ASC",
    "price_desc": "price DESC",
    "most_viewed": "views DESC",
}

OWNER_EDITABLE = {
    "title",
    "description",
    "category",
    "price",
    "unit",
    "quantity",
    "quality",
    "location",
    "images",
}
EDITABLE = OWNER_EDITABLE | {"status"}

JSON_FIELDS = {"location", "images"}


def now() -> datetime:
    return datetime.now(timezone.utc)


def _is_owner_or_staff(user: dict, listing: dict) -> bool:
    role = user.get("role")
    if role in (Role.ADMIN, Role.MODERATOR):
        return True
    return listing.get("seller") == user["_id"]


def _filter_category(db, listing: dict) -> None:
    if not fetch_one(db, "SELECT 1 AS ok FROM categories WHERE slug = %s", (listing.get("category"),)):
        raise ValidationError(f"unknown category '{listing.get('category')}'")


def _coerce(key: str, value):
    if key in JSON_FIELDS and value is not None:
        return Json(value)
    return value


# --------------------------------------------------------------------------- #
def create(db, user: dict, data: dict) -> dict:
    _filter_category(db, data)
    row = insert_returning(
        db,
        f"""
        INSERT INTO listings
            (title, description, category, price, unit, quantity, quality,
             location, images, seller_id, status, views, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'active', 0, %s, %s)
        RETURNING {LISTING_COLS}
        """,
        (
            data["title"].strip(),
            data.get("description", "").strip(),
            data["category"],
            round(float(data["price"]), 2),
            data.get("unit", "unit"),
            float(data["quantity"]),
            data.get("quality"),
            Json({k: v for k, v in data["location"].items() if v}),
            Json(data.get("images", [])),
            user["_id"],
            now(),
            now(),
        ),
    )
    return listing_public(db, row)


def get(db, listing_id: str) -> dict:
    doc = fetch_one(
        db,
        f"SELECT {LISTING_COLS} FROM listings WHERE id = %s AND status <> 'deleted'",
        (listing_id,),
    )
    if doc is None:
        raise NotFound("listing not found")
    bumped = fetch_one(
        db, "UPDATE listings SET views = views + 1 WHERE id = %s RETURNING views", (listing_id,)
    )
    doc["views"] = bumped["views"] if bumped else (doc.get("views") or 0) + 1
    return listing_public(db, doc)


def list_listings(
    db,
    *,
    q: str = "",
    category: str = "",
    min_price: float | None = None,
    max_price: float | None = None,
    city: str = "",
    status: str = "active",
    seller: str = "",
    sort: str = "newest",
    page: int = 1,
    page_size: int = 20,
) -> dict:
    where: list[str] = []
    params: list = []

    if status:
        where.append("status = %s")
        params.append(status)
    else:
        where.append("status <> 'deleted'")

    if min_price is not None:
        where.append("price >= %s")
        params.append(float(min_price))
    if max_price is not None:
        where.append("price <= %s")
        params.append(float(max_price))
    if q:
        where.append("(title ILIKE %s OR description ILIKE %s)")
        like = f"%{q}%"
        params.extend([like, like])
    if category:
        where.append("category = %s")
        params.append(category)
    if city:
        where.append("location->>'city' ILIKE %s")
        params.append(f"%{city}%")
    if seller:
        where.append("seller_id = %s")
        params.append(seller)

    clause = " AND ".join(where)
    total = fetch_one(db, f"SELECT count(*) AS n FROM listings WHERE {clause}", tuple(params))["n"]
    order = SORT_MAP.get(sort, SORT_MAP["newest"])
    rows = fetch_all(
        db,
        f"SELECT {LISTING_COLS} FROM listings WHERE {clause} ORDER BY {order} LIMIT %s OFFSET %s",
        tuple(params) + (page_size, (page - 1) * page_size),
    )
    items = [listing_public(db, d) for d in rows]
    return {"items": items, "total": total, "page": page, "page_size": page_size, "pages": max((total + page_size - 1) // page_size, 1)}


def mine(db, user: dict, page: int = 1, page_size: int = 20) -> dict:
    total = fetch_one(
        db,
        "SELECT count(*) AS n FROM listings WHERE seller_id = %s AND status <> 'deleted'",
        (user["_id"],),
    )["n"]
    rows = fetch_all(
        db,
        f"SELECT {LISTING_COLS} FROM listings WHERE seller_id = %s AND status <> 'deleted' "
        "ORDER BY created_at DESC LIMIT %s OFFSET %s",
        (user["_id"], page_size, (page - 1) * page_size),
    )
    items = [listing_public(db, d) for d in rows]
    return {"items": items, "total": total, "page": page, "page_size": page_size, "pages": max((total + page_size - 1) // page_size, 1)}


def update(db, user: dict, listing_id: str, data: dict) -> dict:
    _get_owned(db, user, listing_id)

    payload = {k: v for k, v in data.items() if k in EDITABLE and v is not None}
    if not payload:
        return listing_public(db, _get(db, listing_id))

    if "category" in payload:
        _filter_category(db, payload)

    if "status" in payload and payload["status"] not in ("sold", "active"):
        raise ValidationError("owner may only set status to 'active' or 'sold'")

    sets = ", ".join(f"{k} = %s" for k in payload)
    params = [_coerce(k, v) for k, v in payload.items()]
    params.extend([now(), listing_id])
    row = fetch_one(
        db,
        f"UPDATE listings SET {sets}, updated_at = %s WHERE id = %s RETURNING {LISTING_COLS}",
        tuple(params),
    )
    return listing_public(db, row)


def delete(db, user: dict, listing_id: str) -> None:
    _get_owned(db, user, listing_id)
    fetch_one(
        db,
        "UPDATE listings SET status = 'deleted', updated_at = %s WHERE id = %s RETURNING id",
        (now(), listing_id),
    )


def report(db, user: dict, listing_id: str, reason: str = "") -> None:
    get(db, listing_id)  # 404 if missing + view bump, matching the original behaviour


def _get(db, listing_id: str) -> dict:
    doc = fetch_one(db, f"SELECT {LISTING_COLS} FROM listings WHERE id = %s", (listing_id,))
    if doc is None:
        raise NotFound("listing not found")
    return doc


def _get_owned(db, user: dict, listing_id: str) -> dict:
    doc = fetch_one(
        db,
        f"SELECT {LISTING_COLS} FROM listings WHERE id = %s AND status <> 'deleted'",
        (listing_id,),
    )
    if doc is None:
        raise NotFound("listing not found")
    if not _is_owner_or_staff(user, doc):
        raise Forbidden("you do not own this listing")
    return doc
