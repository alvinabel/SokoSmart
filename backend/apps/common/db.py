"""Request-scoped PostgreSQL connection for the Flask service.

A single pooled connection is acquired lazily per request, stored on ``flask.g``
and returned to the pool on teardown (see ``apps.factories``).
"""

from __future__ import annotations

from flask import g

from shared.db import acquire, release


def get_db():
    conn = getattr(g, "db", None)
    if conn is None:
        conn = acquire()
        g.db = conn
    return conn


def release_db() -> None:
    conn = getattr(g, "db", None)
    if conn is not None:
        release(conn)
        g.db = None
