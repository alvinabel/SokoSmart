"""Idempotent seeder for demo marketplace content (listings).

Run standalone (from repo root):  ``python api/seed.py``
Requires the backend seeder to have created a demo seller first.
"""

from __future__ import annotations

import os
import random
import sys
from datetime import datetime, timezone

from psycopg.types.json import Json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from shared.db import fetch_one, get_conn, insert_returning  # noqa: E402
from shared.roles import Role  # noqa: E402
from shared.schema import ensure_schema  # noqa: E402

SEED_DEMO_ITEMS = os.getenv("SEED_DEMO_ITEMS", "true").lower() in ("1", "true", "yes")

DEMO_LISTINGS = [
    {"title": "Fresh Watermelon (crate of 10)", "category": "fruits", "price": 2500, "unit": "crate", "quantity": 60, "quality": "Sweet, farm-ripe", "city": "Kumasi"},
    {"title": "Organic Tomatoes", "category": "vegetables", "price": 800, "unit": "basket", "quantity": 120, "quality": "Grade A", "city": "Techiman"},
    {"title": "Yellow Maize (50kg bag)", "category": "grains", "price": 420, "unit": "bag", "quantity": 300, "quality": "Dry, sorted", "city": "Tamale"},
    {"title": "Free-range Eggs", "category": "poultry", "price": 55, "unit": "crate", "quantity": 90, "quality": "Large brown", "city": "Accra"},
    {"title": "Fresh Tilapia", "category": "fisheries", "price": 45, "unit": "kg", "quantity": 200, "quality": "Iced", "city": "Tema"},
    {"title": "Cow Milk (per litre)", "category": "dairy", "price": 15, "unit": "litre", "quantity": 400, "quality": "Pasteurised", "city": "Kumasi"},
    {"title": "Hybrid Cocoa Seedlings", "category": "seeds", "price": 3, "unit": "seedling", "quantity": 5000, "quality": "Hybrid", "city": "Suhum"},
    {"title": "Sun-dried Pepper", "category": "herbs", "price": 120, "unit": "kg", "quantity": 75, "quality": "Sun-dried", "city": "Navrongo"},
]


def now() -> datetime:
    return datetime.now(timezone.utc)


def run(db, seller_email: str = "seller@agrobasket.test") -> dict:
    ensure_schema(db)

    seller = fetch_one(db, "SELECT id AS _id, email FROM users WHERE email = %s", (seller_email,))
    if seller is None:
        seller = fetch_one(db, "SELECT id AS _id, email FROM users WHERE role = %s LIMIT 1", (Role.SELLER,))
    if seller is None:
        return {"listings_created": 0, "reason": "no seller account found; run backend seed first"}

    if not SEED_DEMO_ITEMS:
        return {"listings_created": 0, "reason": "SEED_DEMO_ITEMS disabled"}

    created = 0
    for item in DEMO_LISTINGS:
        if fetch_one(
            db,
            "SELECT 1 AS ok FROM listings WHERE title = %s AND seller_id = %s",
            (item["title"], seller["_id"]),
        ):
            continue
        insert_returning(
            db,
            """
            INSERT INTO listings
                (title, description, category, price, unit, quantity, quality,
                 location, images, seller_id, status, views, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'active', %s, %s, %s)
            RETURNING id
            """,
            (
                item["title"],
                f"{item['title']} available for wholesale and retail. "
                f"Quality: {item['quality']}. Contact seller for bulk pricing.",
                item["category"],
                item["price"],
                item["unit"],
                item["quantity"],
                item["quality"],
                Json({"city": item["city"]}),
                Json([]),
                seller["_id"],
                random.randint(5, 300),
                now(),
                now(),
            ),
        )
        created += 1

    return {"listings_created": created, "seller": seller.get("email")}


if __name__ == "__main__":
    with get_conn() as db:
        print("seed complete:", run(db))
