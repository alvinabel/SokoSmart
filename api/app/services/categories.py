"""Categories domain — read is public, write is moderator/admin."""

from __future__ import annotations

from datetime import datetime, timezone

from shared.db import execute, fetch_all, fetch_one, insert_returning
from shared.errors import Conflict, NotFound


def now() -> datetime:
    return datetime.now(timezone.utc)


def list_categories(db) -> list[dict]:
    rows = fetch_all(db, "SELECT slug, name, emoji, color FROM categories ORDER BY name ASC")
    return [
        {
            "slug": c["slug"],
            "name": c.get("name", c["slug"]),
            "emoji": c.get("emoji", "🥬"),
            "color": c.get("color", "#4CAF50"),
        }
        for c in rows
    ]


def create(db, data: dict) -> dict:
    if fetch_one(db, "SELECT 1 AS ok FROM categories WHERE slug = %s", (data["slug"],)):
        raise Conflict("category slug already exists")
    row = insert_returning(
        db,
        "INSERT INTO categories (slug, name, emoji, color, created_at) VALUES (%s, %s, %s, %s, %s) "
        "RETURNING slug, name, emoji, color",
        (data["slug"], data.get("name", data["slug"]), data.get("emoji", "🥬"), data.get("color", "#4CAF50"), now()),
    )
    return {k: row.get(k) for k in ("slug", "name", "emoji", "color")}


def update(db, slug: str, data: dict) -> dict:
    doc = fetch_one(db, "SELECT slug, name, emoji, color FROM categories WHERE slug = %s", (slug,))
    if doc is None:
        raise NotFound("category not found")
    payload = {k: v for k, v in data.items() if v is not None}
    if payload:
        sets = ", ".join(f"{k} = %s" for k in payload)
        params = list(payload.values()) + [now(), slug]
        row = fetch_one(
            db,
            f"UPDATE categories SET {sets}, updated_at = %s WHERE slug = %s RETURNING slug, name, emoji, color",
            tuple(params),
        )
    else:
        row = doc
    return {k: row.get(k) for k in ("slug", "name", "emoji", "color")}


def delete(db, slug: str) -> None:
    if not execute(db, "DELETE FROM categories WHERE slug = %s", (slug,)):
        raise NotFound("category not found")
