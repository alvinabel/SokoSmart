"""Pytest fixtures — point all services at mongomock via MONGO_TEST=1."""

import os
import sys

os.environ["MONGO_TEST"] = "1"
os.environ["JWT_SECRET"] = "test-secret"
os.environ["MONGO_DB"] = "agrobasket_test"

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pytest  # noqa: E402

from apps.factories import create_app  # noqa: E402


@pytest.fixture()
def app_client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client