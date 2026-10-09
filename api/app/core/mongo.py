"""Database access for the marketplace API.

The service deliberately uses synchronous PyMongo with ``def`` route handlers:
FastAPI runs blocking handlers in a threadpool, keeping the event loop free, and
the same ``mongomock``-backed handle used by tests works here too.
"""

from typing import Any

from shared.mongo import COLLECTIONS, get_db as _shared_get_db


def get_db() -> Any:
    """FastAPI dependency returning the cached Mongo database (see shared/mongo.py)."""
    return _shared_get_db()