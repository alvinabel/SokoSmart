"""Idempotent seeder for the backend data: admin + demo users and categories.

Run standalone (from repo root):  ``python backend/seed.py``
Run via seed service:             ``docker compose --profile tools run --rm seed``

Safe to re-run any number of times — existing rows are kept.
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
from shared.db import fetch_one, get_conn, insert_returning  # noqa: E402
from shared.passwords import hash_password  # noqa: E402
from shared.roles import Role  # noqa: E402
from shared.schema import ensure_schema  # noqa: E402

DEMO_PASSWORD = os.getenv("DEMO_PASSWORD", "Demo@12345")


def now() -> datetime:
    return datetime.now(timezone.utc)


def _ensure_user(db, name: str, email: str, plain_password: str, role: str) -> str:
    if fetch_one(db, "SELECT 1 AS ok FROM users WHERE email = %s", (email,)):
        return "kept"
    insert_returning(
        db,
        """
        INSERT INTO users (name, email, password_hash, role, phone, location, status, verified, created_at, updated_at)
        VALUES (%s, %s, %s, %s, '', '{}'::jsonb, 'active', false, %s, %s)
        RETURNING id
        """,
        (name, email, hash_password(plain_password), role, now(), now()),
    )
    return "created"


def _ensure_categories(db) -> int:
    inserted = 0
    for cat in CATEGORIES:
        row = insert_returning(
            db,
            "INSERT INTO categories (slug, name, emoji, color, created_at) VALUES (%s, %s, %s, %s, %s) "
            "ON CONFLICT (slug) DO NOTHING RETURNING slug",
            (cat["slug"], cat.get("name", cat["slug"]), cat.get("emoji", "🥬"), cat.get("color", "#4CAF50"), now()),
        )
        if row is not None:
            inserted += 1
    return inserted


def run(db, *, demo_users: bool = True) -> dict:
    ensure_schema(db)

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
    with get_conn() as db:
        outcome = run(db)
    print("seed complete:", outcome)
