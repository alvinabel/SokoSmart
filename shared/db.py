"""PostgreSQL data access shared by every service.

This replaces the former PyMongo layer. A process-wide connection pool
(``psycopg_pool``) hands out short-lived connections and the services issue plain
parameterised SQL. Rows are returned as ``dict``s (``dict_row`` row factory), so
the service/serializer code keeps working with mapping-style access.

Connections are opened in autocommit mode: every statement commits immediately,
matching the previous document-store semantics (each ``insert_one`` /
``update_one`` was already durable).
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Mapping, Sequence

from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from .config import get_config

_pool: ConnectionPool | None = None


def get_pool() -> ConnectionPool:
    """Return the cached connection pool (lazily created, opened once)."""
    global _pool
    if _pool is None:
        cfg = get_config()
        _pool = ConnectionPool(
            conninfo=cfg.database_url,
            min_size=1,
            max_size=cfg.db_pool_max,
            open=True,
            kwargs={"row_factory": dict_row, "autocommit": True},
        )
    return _pool


def acquire():
    """Check a connection out of the pool."""
    return get_pool().getconn()


def release(conn) -> None:
    """Return a connection to the pool (no-op for ``None``)."""
    if conn is not None:
        get_pool().putconn(conn)


@contextmanager
def get_conn():
    """Context manager yielding a pooled connection (always returned)."""
    conn = acquire()
    try:
        yield conn
    finally:
        release(conn)


def reset_pool() -> None:
    """Close and drop the pool. Used by tests when the database URL changes."""
    global _pool
    if _pool is not None:
        _pool.close()
        _pool = None


# --------------------------------------------------------------------------- #
# Thin query helpers
# --------------------------------------------------------------------------- #
def fetch_all(conn, sql: str, params=()) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def fetch_one(conn, sql: str, params=()) -> dict | None:
    with conn.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchone()


def execute(conn, sql: str, params=()) -> int:
    """Run a statement and return the affected row count."""
    with conn.cursor() as cur:
        cur.execute(sql, params)
        return cur.rowcount


def insert_returning(conn, sql: str, params=()) -> dict | None:
    """Run an ``INSERT ... RETURNING ...`` and return the first row (or ``None``)."""
    with conn.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchone()
