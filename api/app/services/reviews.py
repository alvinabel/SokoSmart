"""Reviews domain — a buyer may review a seller once per completed order."""

from __future__ import annotations

from datetime import datetime, timezone

from bson import ObjectId
from pymongo import DESCENDING

from shared.errors import Conflict, Forbidden, NotFound
from shared.mongo import COLLECTIONS
from shared.roles import Role

from .notifications import notify


def now() -> datetime:
    return datetime.now(timezone.utc)


def _public(db, review: dict) -> dict:
    author = db[COLLECTIONS["users"]].find_one({"_id": review.get("author")})
    return {
        "id": str(review["_id"]),
        "listing_id": str(review.get("listing")),
        "rating": review.get("rating", 0),
        "comment": review.get("comment", ""),
        "author": {"id": str(author["_id"]), "name": author.get("name", "")} if author else None,
        "created_at": review.get("created_at").isoformat() if review.get("created_at") else None,
    }


def _recompute_seller_rating(db, seller_id: ObjectId) -> None:
    reviews = list(db[COLLECTIONS["reviews"]].find({"seller": seller_id}))
    count = len(reviews)
    avg = round(sum(r.get("rating", 0) for r in reviews) / count, 2) if count else 0
    db[COLLECTIONS["users"]].update_one(
        {"_id": seller_id}, {"$set": {"rating": {"avg": avg, "count": count}, "updated_at": now()}}
    )


def create(db, user: dict, listing_id: str, rating: int, comment: str | None) -> dict:
    try:
        listing = db[COLLECTIONS["listings"]].find_one({"_id": ObjectId(listing_id)})
    except Exception as exc:
        raise NotFound("listing not found") from exc
    if listing is None:
        raise NotFound("listing not found")

    completed = db[COLLECTIONS["orders"]].find_one(
        {"listing": listing["_id"], "buyer": user["_id"], "status": "completed"}
    )
    if completed is None:
        raise Forbidden("you can only review after a completed order")

    if db[COLLECTIONS["reviews"]].find_one({"listing": listing["_id"], "author": user["_id"]}):
        raise Conflict("you have already reviewed this listing")

    doc = {
        "listing": listing["_id"],
        "author": user["_id"],
        "seller": listing["seller"],
        "rating": int(rating),
        "comment": (comment or "").strip(),
        "created_at": now(),
    }
    result = db[COLLECTIONS["reviews"]].insert_one(doc)
    doc["_id"] = result.inserted_id
    _recompute_seller_rating(db, listing["seller"])
    notify(db, str(listing["seller"]), "review.new", {"listing_id": str(listing["_id"]), "rating": rating})
    return _public(db, doc)


def list_for_listing(db, listing_id: str, page: int = 1, page_size: int = 20) -> dict:
    try:
        oid = ObjectId(listing_id)
    except Exception as exc:
        raise NotFound("listing not found") from exc
    coll = db[COLLECTIONS["reviews"]]
    query = {"listing": oid}
    total = coll.count_documents(query)
    cursor = coll.find(query).sort("created_at", DESCENDING).skip((page - 1) * page_size).limit(page_size)
    items = [_public(db, r) for r in cursor]
    return {"items": items, "total": total, "page": page, "page_size": page_size, "pages": max((total + page_size - 1) // page_size, 1)}


def seller_summary(db, seller_id: str, page: int = 1, page_size: int = 10) -> dict:
    try:
        oid = ObjectId(seller_id)
    except Exception as exc:
        raise NotFound("user not found") from exc
    coll = db[COLLECTIONS["reviews"]]
    query = {"seller": oid}
    total = coll.count_documents(query)
    reviews = list(coll.find(query))
    avg = round(sum(r.get("rating", 0) for r in reviews) / total, 2) if total else 0
    cursor = coll.find(query).sort("created_at", DESCENDING).skip((page - 1) * page_size).limit(page_size)
    return {
        "avg_rating": avg,
        "count": total,
        "items": [_public(db, r) for r in cursor],
    }


def delete(db, user: dict, review_id: str) -> None:
    try:
        review = db[COLLECTIONS["reviews"]].find_one({"_id": ObjectId(review_id)})
    except Exception as exc:
        raise NotFound("review not found") from exc
    if review is None:
        raise NotFound("review not found")
    if review.get("author") != user["_id"] and user.get("role") != Role.ADMIN:
        raise Forbidden("you cannot delete this review")
    db[COLLECTIONS["reviews"]].delete_one({"_id": review["_id"]})
    _recompute_seller_rating(db, review["seller"])