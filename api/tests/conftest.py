"""Pytest fixtures for the marketplace API (PostgreSQL-backed TestClient)."""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))          # api/tests
API_DIR = os.path.dirname(BASE)                            # api
ROOT = os.path.dirname(API_DIR)                            # repo root
for _p in (API_DIR, ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("ADMIN_EMAIL", "admin@test.io")
os.environ.setdefault("ADMIN_PASSWORD", "Admin@12345")

from shared.testing import ensure_test_database  # noqa: E402

ensure_test_database()

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.api import create_app  # noqa: E402
from shared.db import get_conn, insert_returning  # noqa: E402
from shared.jwt_token import create_access_token  # noqa: E402
from shared.passwords import hash_password  # noqa: E402
from shared.roles import Role  # noqa: E402
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
def client():
    with TestClient(create_app()) as test_client:
        yield test_client


def make_user(role: str = Role.SELLER, email: str = "seller@test.io", name: str = "Seller"):
    with get_conn() as db:
        user = insert_returning(
            db,
            "INSERT INTO users (name, email, password_hash, role, status, verified, created_at) "
            "VALUES (%s, %s, %s, %s, 'active', true, now()) "
            "RETURNING id AS _id, name, email, role, status",
            (name, email, hash_password("Password@1"), role),
        )
    token = create_access_token(user)
    return user, {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def seller():
    return make_user(Role.SELLER, "seller@test.io", "Seller")


@pytest.fixture()
def buyer():
    return make_user(Role.BUYER, "buyer@test.io", "Buyer")
