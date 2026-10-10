"""Dependencies: current user resolution and permission gates.

JWT verification is shared with the Flask identity service via ``shared.jwt_token``
(a single ``JWT_SECRET``), so an access token minted at ``/api/auth/login`` is
accepted here without any network call.
"""

from __future__ import annotations

from typing import Callable

import jwt as pyjwt
from fastapi import Depends, Header

from shared.errors import Forbidden, Unauthorized
from shared.jwt_token import decode_token
from shared.roles import user_has

from .core.db import get_db
from .services.serializers import get_user


def _user_from_bearer(authorization: str, db) -> dict | None:
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    try:
        claims = decode_token(token, expected_type="access")
    except pyjwt.PyJWTError:
        return None
    return get_user(db, claims.get("sub"))


def get_current_user(authorization: str = Header(""), db=Depends(get_db)) -> dict:
    user = _user_from_bearer(authorization, db)
    if user is None:
        raise Unauthorized("invalid or expired token")
    if user.get("status") == "suspended":
        raise Forbidden("account is suspended")
    return user


def get_optional_user(authorization: str = Header(""), db=Depends(get_db)) -> dict | None:
    user = _user_from_bearer(authorization, db)
    if user is None or user.get("status") == "suspended":
        return None
    return user


def require_permission(permission: str) -> Callable:
    """Factory returning a dependency that checks ``permission`` against the role."""

    def _check(user: dict = Depends(get_current_user)) -> dict:
        if not user_has(user.get("role"), permission):
            raise Forbidden(f"permission '{permission}' is required")
        return user

    return _check
