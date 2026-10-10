"""Shared-library unit tests (no Mongo required)."""

import os
import sys

os.environ["MONGO_TEST"] = "1"
os.environ["JWT_SECRET"] = "test-secret"

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pytest  # noqa: E402

from shared.jwt_token import create_access_token, create_refresh_token, decode_token  # noqa: E402
from shared.passwords import hash_password, verify_password  # noqa: E402
from shared.roles import Role, PERMISSIONS, user_has  # noqa: E402


def test_password_roundtrip():
    hashed = hash_password("Sup3rSecret")
    assert hashed != "Sup3rSecret"
    assert verify_password("Sup3rSecret", hashed)
    assert not verify_password("wrong", hashed)


def test_access_token_roundtrip():
    user = {"_id": "65abc", "name": "Ada", "email": "a@b.io", "role": Role.SELLER}
    token = create_access_token(user)
    claims = decode_token(token, expected_type="access")
    assert claims["sub"] == "65abc"
    assert claims["role"] == Role.SELLER
    assert claims["typ"] == "access"


def test_refresh_token_type_enforced():
    user = {"_id": "65abc"}
    token, jti = create_refresh_token(str(user["_id"]))
    claims = decode_token(token, expected_type="refresh")
    assert claims["jti"] == jti
    with pytest.raises(Exception):
        decode_token(token, expected_type="access")


def test_role_matrix_consistency():
    assert user_has(Role.BUYER, "listing.read")
    assert not user_has(Role.BUYER, "listing.manage")
    assert user_has(Role.SELLER, "listing.manage")
    assert user_has(Role.ADMIN, "listing.moderate")
    assert user_has(Role.MODERATOR, "stats.read")
    for permission in PERMISSIONS[Role.ADMIN]:
        assert user_has(Role.ADMIN, permission)