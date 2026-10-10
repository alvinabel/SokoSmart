"""Minimal PyMongo bootstrap: client factory + index creation.

Used by the Flask service, seeders and maintenance scripts. The FastAPI async
service uses its own Motor wrapper (``api/app/core/mongo.py``) because Motor is
asynchronous — the index definitions live here so both stay in sync.
"""

from __future__ import annotations

import os

from pymongo import ASCENDING, DESCENDING, IndexModel, MongoClient

from .config import get_config

# Collection names used across both services (single source of truth).
COLLECTIONS = {
    "users": "users",
    "refresh_tokens": "refresh_tokens",
    "listings": "listings",
    "categories": "categories",
    "orders": "orders",
    "bids": "bids",
    "reviews": "reviews",
    "favorites": "favorites",
    "notifications": "notifications",
    "messages": "messages",
    "audit_logs": "audit_logs",
}


_client = None
_MONGO_TEST = "MONGO_TEST" in os.environ
if _MONGO_TEST:
    import mongomock  # noqa: F401  (test-only dependency)


def get_db():
    """Return a cached database handle (one client per process).

    When ``MONGO_TEST=1`` (used by pytest) a mongomock client is returned instead.
    """
    global _client
    cfg = get_config()
    if _client is None:
        if _MONGO_TEST:
            _client = mongomock.MongoClient()
        else:
            _client = MongoClient(cfg.mongo_uri)
    return _client[cfg.mongo_db]


def ensure_indexes(db) -> None:
    """Idempotent — safe to call on every boot."""
    users = db[COLLECTIONS["users"]]
    users.create_indexes(
        [
            IndexModel([("email", ASCENDING)], unique=True),
            IndexModel([("role", ASCENDING)]),
        ]
    )

    db[COLLECTIONS["refresh_tokens"]].create_index(
        [("jti", ASCENDING)], unique=True, expireAfterSeconds=86400 * 30
    )

    listings = db[COLLECTIONS["listings"]]
    listings.create_indexes(
        [
            IndexModel([("title", "text"), ("description", "text")], default_language="english"),
            IndexModel([("category", ASCENDING)]),
            IndexModel([("seller", ASCENDING)]),
            IndexModel([("status", ASCENDING)]),
            IndexModel([("price", ASCENDING)]),
            IndexModel([("location.city", ASCENDING)]),
            IndexModel([("created_at", DESCENDING)]),
            IndexModel([("_fts_status", ASCENDING)]),
        ]
    )

    db[COLLECTIONS["orders"]].create_indexes(
        [
            IndexModel([("buyer", ASCENDING)]),
            IndexModel([("seller", ASCENDING)]),
            IndexModel([("listing", ASCENDING)]),
            IndexModel([("status", ASCENDING)]),
        ]
    )

    db[COLLECTIONS["bids"]].create_indexes(
        [
            IndexModel([("listing", ASCENDING)]),
            IndexModel([("bidder", ASCENDING)]),
            IndexModel([("status", ASCENDING)]),
        ]
    )

    reviews = db[COLLECTIONS["reviews"]]
    reviews.create_indexes(
        [
            IndexModel([("listing", ASCENDING)]),
            IndexModel([("seller", ASCENDING)]),
            IndexModel([("listing", ASCENDING), ("author", ASCENDING)], unique=True),
        ]
    )

    db[COLLECTIONS["favorites"]].create_indexes(
        [
            IndexModel([("user", ASCENDING), ("listing", ASCENDING)], unique=True),
            IndexModel([("listing", ASCENDING)]),
        ]
    )

    db[COLLECTIONS["notifications"]].create_indexes(
        [
            IndexModel([("recipient", ASCENDING), ("read", ASCENDING)]),
            IndexModel([("created_at", DESCENDING)]),
        ]
    )

    messages = db[COLLECTIONS["messages"]]
    messages.create_indexes(
        [
            IndexModel([("conversation", ASCENDING), ("created_at", ASCENDING)]),
            IndexModel([("sender", ASCENDING)]),
        ]
    )

    db[COLLECTIONS["audit_logs"]].create_index([("created_at", DESCENDING)])
    db[COLLECTIONS["categories"]].create_index([("slug", ASCENDING)], unique=True)