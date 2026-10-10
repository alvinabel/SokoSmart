"""Database access for the marketplace API.

The service uses synchronous psycopg with ``def`` route handlers: FastAPI runs
blocking handlers in a threadpool, keeping the event loop free. ``get_db`` is a
dependency that checks a pooled connection out for the lifetime of a request.
"""

from __future__ import annotations

from shared.db import get_conn


def get_db():
    """FastAPI dependency yielding one pooled PostgreSQL connection per request."""
    with get_conn() as conn:
        yield conn
