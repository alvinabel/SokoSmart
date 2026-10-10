"""Idempotent seeder for demo marketplace content (listings).

Run standalone (from repo root):  ``python api/seed.py``
Requires the backend seeder to have created a demo seller first.
"""

from __future__ import annotations

import os
import random
import sys
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from shared.mongo import COLLECTIONS, ensure_indexes, get_db  # noqa: E402
from shared.roles import Role  # noqa: E402

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
    ensure_indexes(db)

    seller = db[COLLECTIONS["users"]].find_one({"email": seller_email})
    if seller is None:
        seller = db[COLLECTIONS["users"]].find_one({"role": Role.SELLER})
    if seller is None:
        return {"listings_created": 0, "reason": "no seller account found; run backend seed first"}

    if not SEED_DEMO_ITEMS:
        return {"listings_created": 0, "reason": "SEED_DEMO_ITEMS disabled"}

    created = 0
    for item in DEMO_LISTINGS:
        exists = db[COLLECTIONS["listings"]].find_one(
            {"title": item["title"], "seller": seller["_id"]}
        )
        if exists:
            continue
        db[COLLECTIONS["listings"]].insert_one(
            {
                "title": item["title"],
                "description": f"{item['title']} available for wholesale and retail. "
                f"Quality: {item['quality']}. Contact seller for bulk pricing.",
                "category": item["category"],
                "price": item["price"],
                "unit": item["unit"],
                "quantity": item["quantity"],
                "quality": item["quality"],
                "location": {"city": item["city"]},
                "images": [],
                "seller": seller["_id"],
                "status": "active",
                "views": random.randint(5, 300),
                "created_at": now(),
                "updated_at": now(),
            }
        )
        created += 1

    return {"listings_created": created, "seller": seller.get("email")}


if __name__ == "__main__":
    print("seed complete:", run(get_db()))