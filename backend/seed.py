"""Idempotent seeder for the backend data: admin + demo users and categories.

Run standalone (from repo root):  ``python backend/seed.py``
Run via seed service:             ``docker compose --profile tools run --rm seed``

Safe to re-run any number of times — existing documents are kept.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from shared.categories import CATEGORIES  # noqa: E402
from shared.mongo import COLLECTIONS, ensure_indexes, get_db  # noqa: E402
from shared.passwords import hash_password  # noqa: E402
from shared.roles import Role  # noqa: E402

DEMO_PASSWORD = os.getenv("DEMO_PASSWORD", "Demo@12345")


def now() -> datetime:
    return datetime.now(timezone.utc)


def _ensure_user(db, name: str, email: str, plain_password: str, role: str) -> str:
    existing = db[COLLECTIONS["users"]].find_one({"email": email})
    if existing:
        return "kept"
    db[COLLECTIONS["users"]].insert_one(
        {
            "name": name,
            "email": email,
            "password_hash": hash_password(plain_password),
            "role": role,
            "phone": "",
            "location": {},
            "status": "active",
            "verified": False,
            "created_at": now(),
            "updated_at": now(),
        }
    )
    return "created"


def _ensure_categories(db) -> int:
    inserted = 0
    for cat in CATEGORIES:
        if db[COLLECTIONS["categories"]].find_one({"slug": cat["slug"]}):
            continue
        db[COLLECTIONS["categories"]].insert_one({**cat, "created_at": now()})
        inserted += 1
    return inserted


def run(db, *, demo_users: bool = True) -> dict:
    ensure_indexes(db)

    admin_email = os.getenv("ADMIN_EMAIL", "admin@agrobasket.test")
    admin_password = os.getenv("ADMIN_PASSWORD", "Admin@12345")

    results = {
        "admin": _ensure_user(db, "Platform Admin", admin_email, admin_password, Role.ADMIN),
        "categories_created": _ensure_categories(db),
    }

    if demo_users:
        results["seller"] = _ensure_user(db, "Demo Farmer", "seller@agrobasket.test", DEMO_PASSWORD, Role.SELLER)
        results["buyer"] = _ensure_user(db, "Demo Buyer", "buyer@agrobasket.test", DEMO_PASSWORD, Role.BUYER)

    return results


if __name__ == "__main__":
    db = get_db()
    outcome = run(db)
    print("seed complete:", outcome)