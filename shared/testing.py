"""Test-only helpers: resolve (or start) the PostgreSQL database used by the suites.

Order of preference:
  1. ``DATABASE_URL`` from the environment (used in CI / against Supabase).
  2. An embedded PostgreSQL bundled by the optional ``pgserver`` dev dependency,
     started once per session in a temp directory.

``ensure_test_database`` must be called *before* anything imports ``shared.config``
(or clears its ``lru_cache``) because the URL is cached on first access.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

_server = None


def ensure_test_database() -> str:
    """Return a usable ``DATABASE_URL``, starting an embedded server if necessary."""
    global _server

    url = (os.getenv("DATABASE_URL") or "").strip()
    if url:
        return url

    try:
        import pgserver
    except ImportError as exc:  # pragma: no cover - exercised only without pgserver
        raise RuntimeError(
            "No DATABASE_URL is set and the optional 'pgserver' package is not "
            "installed. Either set DATABASE_URL to a PostgreSQL instance or install "
            "the dev requirements (pip install pgserver)."
        ) from exc

    pgdata = Path(tempfile.gettempdir()) / "opencode" / "pgdata"
    pgdata.parent.mkdir(parents=True, exist_ok=True)

    _server = pgserver.get_server(str(pgdata), cleanup_mode="stop")
    url = _server.get_uri()
    os.environ["DATABASE_URL"] = url
    return url
