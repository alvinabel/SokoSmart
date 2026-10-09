"""Listings domain — CRUD, search/filter, view counting, ownership rules."""

from __future__ import annotations

from datetime import datetime, timezone

from bson import ObjectId
from pymongo import ASCENDING, DESCENDING

from shared.errors import Forbidden, NotFound, ValidationError
from shared.mongo import COLLECTIONS
from shared.roles import Role

from .serializers import listing_public

SORT_MAP = {
    "newest": [("created_at", DESCENDING)],
    "price_asc": [("price", ASCENDING)],
    "price_desc": [("price", DESCENDING)],
    "most_viewed": [("views", DESCENDING)],
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


def now() -> datetime:
    return datetime.now(timezone.utc)


def _is_owner_or_staff(user: dict, listing: dict) -> bool:
    role = user.get("role")
    if role in (Role.ADMIN, Role.MODERATOR):
        return True
    return listing.get("seller") == user["_id"]


def _filter_category(db, listing: dict) -> None:
    if not db[COLLECTIONS["categories"]].find_one({"slug": listing.get("category")}):
        raise ValidationError(f"unknown category '{listing.get('category')}'")


# --------------------------------------------------------------------------- #
def create(db, user: dict, data: dict) -> dict:
    _filter_category(db, data)
    doc = {
        "title": data["title"].strip(),
        "description": data.get("description", "").strip(),
        "category": data["category"],
        "price": round(float(data["price"]), 2),
        "unit": data.get("unit", "unit"),
        "quantity": float(data["quantity"]),
        "quality": data.get("quality"),
        "location": {k: v for k, v in data["location"].items() if v},
        "images": data.get("images", []),
        "seller": user["_id"],
        "status": "active",
        "views": 0,
        "created_at": now(),
        "updated_at": now(),
    }
    result = db[COLLECTIONS["listings"]].insert_one(doc)
    doc["_id"] = result.inserted_id
    return listing_public(db, doc)


def get(db, listing_id: str) -> dict:
    doc = db[COLLECTIONS["listings"]].find_one({"_id": _oid(listing_id)})
    if doc is None or doc.get("status") == "deleted":
        raise NotFound("listing not found")
    db[COLLECTIONS["listings"]].update_one({"_id": doc["_id"]}, {"$inc": {"views": 1}})
    doc["views"] = (doc.get("views") or 0) + 1
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
    query: dict = {"status": status} if status else {"status": {"$ne": "deleted"}}

    price_filter: dict = {}
    if min_price is not None:
        price_filter["$gte"] = float(min_price)
    if max_price is not None:
        price_filter["$lte"] = float(max_price)
    if price_filter:
        query["price"] = price_filter

    if q:
        query["$or"] = [
            {"title": {"$regex": q, "$options": "i"}},
            {"description": {"$regex": q, "$options": "i"}},
        ]
    if category:
        query["category"] = category
    if city:
        query["location.city"] = {"$regex": city, "$options": "i"}
    if seller:
        query["seller"] = ObjectId(seller)

    coll = db[COLLECTIONS["listings"]]
    total = coll.count_documents(query)
    sort_spec = SORT_MAP.get(sort, SORT_MAP["newest"])
    cursor = coll.find(query).sort(sort_spec).skip((page - 1) * page_size).limit(page_size)

    docs = list(cursor)
    return {
        "items": [listing_public(db, d) for d in docs],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": max((total + page_size - 1) // page_size, 1),
    }


def mine(db, user: dict, page: int = 1, page_size: int = 20) -> dict:
    coll = db[COLLECTIONS["listings"]]
    query = {"seller": user["_id"], "status": {"$ne": "deleted"}}
    total = coll.count_documents(query)
    cursor = coll.find(query).sort("created_at", DESCENDING).skip((page - 1) * page_size).limit(page_size)
    return {
        "items": [listing_public(db, d) for d in cursor],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": max((total + page_size - 1) // page_size, 1),
    }


def update(db, user: dict, listing_id: str, data: dict) -> dict:
    doc = _get_owned(db, user, listing_id)

    payload = {k: v for k, v in data.items() if k in EDITABLE and v is not None}
    if not payload:
        return listing_public(db, doc)

    if "category" in payload:
        _filter_category(db, payload)

    if "status" in payload:
        status = payload["status"]
        if status not in ("sold", "active"):
            raise ValidationError("owner may only set status to 'active' or 'sold'")

    payload["updated_at"] = now()
    db[COLLECTIONS["listings"]].update_one({"_id": doc["_id"]}, {"$set": payload})
    return listing_public(db, db[COLLECTIONS["listings"]].find_one({"_id": doc["_id"]}))


def delete(db, user: dict, listing_id: str) -> None:
    doc = _get_owned(db, user, listing_id)
    db[COLLECTIONS["listings"]].update_one(
        {"_id": doc["_id"]}, {"$set": {"status": "deleted", "updated_at": now()}}
    )


def report(db, user: dict, listing_id: str, reason: str = "") -> None:
    doc = get(db, listing_id)
    db[COLLECTIONS["listings"]].update_one(
        {"_id": doc["_id"]},
        {"$set": {"reported": True, "reported_reason": reason, "reported_by": user["_id"]}},
    )


def _oid(listing_id: str) -> ObjectId:
    try:
        return ObjectId(listing_id)
    except Exception as exc:
        raise NotFound("listing not found") from exc


def _get_owned(db, user: dict, listing_id: str) -> dict:
    doc = db[COLLECTIONS["listings"]].find_one({"_id": _oid(listing_id)})
    if doc is None or doc.get("status") == "deleted":
        raise NotFound("listing not found")
    if not _is_owner_or_staff(user, doc):
        raise Forbidden("you do not own this listing")
    return doc