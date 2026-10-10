"""Pytest fixtures — PostgreSQL-backed Flask test client."""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))          # backend/tests
BACKEND_DIR = os.path.dirname(BASE)                        # backend
ROOT = os.path.dirname(BACKEND_DIR)                        # repo root
for _p in (BACKEND_DIR, ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("ADMIN_EMAIL", "admin@test.io")
os.environ.setdefault("ADMIN_PASSWORD", "Admin@12345")

from shared.testing import ensure_test_database  # noqa: E402

ensure_test_database()

import pytest  # noqa: E402

from apps.factories import create_app  # noqa: E402
from shared.db import get_conn  # noqa: E402
from shared.schema import ensure_schema, truncate_all  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _schema():
    with get_conn() as db:
        ensure_schema(db)
    yield


@pytest.fixture(autouse=True)
def clean_db():
    with get_conn() as db:
        truncate_all(db)
    yield


@pytest.fixture()
def app_client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client
