"""Reviews domain — a buyer may review a seller once per completed order."""

from __future__ import annotations

from datetime import datetime, timezone

from psycopg.types.json import Json

from shared.db import execute, fetch_all, fetch_one, insert_returning
from shared.errors import Conflict, Forbidden, NotFound
from shared.roles import Role

from .notifications import notify
from .serializers import get_listing_row, get_user

REVIEW_COLS = "id AS _id, listing_id AS listing, author_id AS author, seller_id AS seller, rating, comment, created_at"


def now() -> datetime:
    return datetime.now(timezone.utc)


def _public(db, review: dict) -> dict:
    author = get_user(db, review.get("author"))
    return {
        "id": str(review["_id"]),
        "listing_id": str(review.get("listing")),
        "rating": review.get("rating", 0),
        "comment": review.get("comment", ""),
        "author": {"id": str(author["_id"]), "name": author.get("name", "")} if author else None,
        "created_at": review.get("created_at").isoformat() if review.get("created_at") else None,
    }


def _recompute_seller_rating(db, seller_id: str) -> None:
    stats = fetch_one(
        db, "SELECT count(*) AS n, coalesce(avg(rating), 0) AS avg FROM reviews WHERE seller_id = %s", (seller_id,)
    )
    avg = round(float(stats["avg"]), 2) if stats["n"] else 0
    fetch_one(
        db,
        "UPDATE users SET rating = %s, updated_at = %s WHERE id = %s RETURNING id",
        (Json({"avg": avg, "count": stats["n"]}), now(), seller_id),
    )


def create(db, user: dict, listing_id: str, rating: int, comment: str | None) -> dict:
    listing = fetch_one(db, "SELECT id AS _id, seller_id AS seller FROM listings WHERE id = %s", (listing_id,))
    if listing is None:
        raise NotFound("listing not found")

    completed = fetch_one(
        db,
        "SELECT 1 AS ok FROM orders WHERE listing_id = %s AND buyer_id = %s AND status = 'completed'",
        (listing["_id"], user["_id"]),
    )
    if completed is None:
        raise Forbidden("you can only review after a completed order")

    if fetch_one(
        db,
        "SELECT 1 AS ok FROM reviews WHERE listing_id = %s AND author_id = %s",
        (listing["_id"], user["_id"]),
    ):
        raise Conflict("you have already reviewed this listing")

    row = insert_returning(
        db,
        f"""
        INSERT INTO reviews (listing_id, author_id, seller_id, rating, comment, created_at)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id AS _id, listing_id AS listing, author_id AS author, seller_id AS seller, rating, comment, created_at
        """,
        (listing["_id"], user["_id"], listing["seller"], int(rating), (comment or "").strip(), now()),
    )
    _recompute_seller_rating(db, listing["seller"])
    notify(db, str(listing["seller"]), "review.new", {"listing_id": str(listing["_id"]), "rating": rating})
    return _public(db, row)


def list_for_listing(db, listing_id: str, page: int = 1, page_size: int = 20) -> dict:
    total = fetch_one(db, "SELECT count(*) AS n FROM reviews WHERE listing_id = %s", (listing_id,))["n"]
    rows = fetch_all(
        db,
        f"SELECT id AS _id, listing_id AS listing, author_id AS author, seller_id AS seller, rating, comment, created_at "
        "FROM reviews WHERE listing_id = %s ORDER BY created_at DESC LIMIT %s OFFSET %s",
        (listing_id, page_size, (page - 1) * page_size),
    )
    items = [_public(db, r) for r in rows]
    return {"items": items, "total": total, "page": page, "page_size": page_size, "pages": max((total + page_size - 1) // page_size, 1)}


def seller_summary(db, seller_id: str, page: int = 1, page_size: int = 10) -> dict:
    stats = fetch_one(
        db, "SELECT count(*) AS n, avg(rating) AS avg FROM reviews WHERE seller_id = %s", (seller_id,)
    )
    total = stats["n"]
    avg = round(float(stats["avg"]), 2) if total and stats["avg"] is not None else 0
    rows = fetch_all(
        db,
        "SELECT id AS _id, listing_id AS listing, author_id AS author, seller_id AS seller, rating, comment, created_at "
        "FROM reviews WHERE seller_id = %s ORDER BY created_at DESC LIMIT %s OFFSET %s",
        (seller_id, page_size, (page - 1) * page_size),
    )
    return {"avg_rating": avg, "count": total, "items": [_public(db, r) for r in rows]}


def delete(db, user: dict, review_id: str) -> None:
    review = fetch_one(
        db, "SELECT id AS _id, seller_id AS seller, author_id AS author FROM reviews WHERE id = %s", (review_id,)
    )
    if review is None:
        raise NotFound("review not found")
    if review.get("author") != user["_id"] and user.get("role") != Role.ADMIN:
        raise Forbidden("you cannot delete this review")
    execute(db, "DELETE FROM reviews WHERE id = %s", (review["_id"],))
    _recompute_seller_rating(db, review["seller"])
