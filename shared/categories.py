"""Canonical marketplace seed data.

Shared so that ``backend/seed.py``, ``api/seed.py`` and the UI fallback constants
stay in agreement. Categories use the watermelon palette hints for badges.
"""

from __future__ import annotations

CATEGORIES = [
    {"slug": "vegetables", "name": "Vegetables", "emoji": "🥦", "color": "#4CAF50"},
    {"slug": "fruits", "name": "Fruits", "emoji": "🍉", "color": "#F4435E"},
    {"slug": "grains", "name": "Grains & Cereals", "emoji": "🌾", "color": "#216E39"},
    {"slug": "livestock", "name": "Livestock", "emoji": "🐄", "color": "#FF758F"},
    {"slug": "poultry", "name": "Poultry", "emoji": "🐔", "color": "#F4435E"},
    {"slug": "dairy", "name": "Dairy", "emoji": "🥛", "color": "#4CAF50"},
    {"slug": "fisheries", "name": "Fisheries", "emoji": "🐟", "color": "#216E39"},
    {"slug": "herbs", "name": "Herbs & Spices", "emoji": "🌿", "color": "#4CAF50"},
    {"slug": "seeds", "name": "Seeds & Seedlings", "emoji": "🌱", "color": "#216E39"},
    {"slug": "processed", "name": "Processed Goods", "emoji": "🧺", "color": "#FF758F"},
]

CATEGORY_SLUGS = [c["slug"] for c in CATEGORIES]


def category_by_slug(slug: str) -> dict | None:
    return next((c for c in CATEGORIES if c["slug"] == slug), None)