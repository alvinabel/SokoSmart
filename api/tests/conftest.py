"""Pytest fixtures for the marketplace API (mongomock-backed TestClient)."""

import os
import sys
from datetime import datetime, timezone

os.environ["MONGO_TEST"] = "1"
os.environ["JWT_SECRET"] = "test-secret"
os.environ["MONGO_DB"] = "agrobasket_test"

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.api import create_app  # noqa: E402
from shared.jwt_token import create_access_token  # noqa: E402
from shared.mongo import COLLECTIONS, get_db  # noqa: E402
from shared.passwords import hash_password  # noqa: E402
from shared.roles import Role  # noqa: E402


@pytest.fixture(autouse=True)
def clean_db():
    db = get_db()
    for name in COLLECTIONS.values():
        db.drop_collection(name)
    yield


@pytest.fixture()
def client():
    with TestClient(create_app()) as test_client:
        yield test_client


def make_user(role: str = Role.SELLER, email: str = "seller@test.io", name: str = "Seller"):
    db = get_db()
    result = db[COLLECTIONS["users"]].insert_one(
        {
            "name": name,
            "email": email,
            "password_hash": hash_password("Password@1"),
            "role": role,
            "phone": "",
            "location": {},
            "status": "active",
            "verified": True,
            "created_at": datetime.now(timezone.utc),
        }
    )
    user = db[COLLECTIONS["users"]].find_one({"_id": result.inserted_id})
    token = create_access_token(user)
    return user, {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def seller():
    return make_user(Role.SELLER, "seller@test.io", "Seller")


@pytest.fixture()
def buyer():
    return make_user(Role.BUYER, "buyer@test.io", "Buyer")