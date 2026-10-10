"""Flask decorators: ``@jwt_required`` and ``@require_permission(...)``.

Both decorators attach the requested user to ``flask.g.user`` so handlers and
services can read ``g.user["_id"]`` / ``g.user["role"]``.
"""

from functools import wraps

import jwt as pyjwt
from flask import g, request

from shared.errors import Forbidden, Unauthorized
from shared.jwt_token import decode_token
from shared.roles import user_has as _user_has

from .db import get_db

USER_COLS = "id AS _id, name, email, role, phone, bio, location, status, verified, rating, created_at"


def jwt_required(fn):
    """Verify ``Authorization: Bearer <access-token>`` and attach the user to ``g.user``."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        header = request.headers.get("Authorization", "")
        scheme, _, token = header.partition(" ")
        if scheme.lower() != "bearer" or not token:
            raise Unauthorized("missing bearer token")

        try:
            claims = decode_token(token, expected_type="access")
        except pyjwt.PyJWTError as exc:
            raise Unauthorized("invalid or expired token") from exc

        from shared.db import fetch_one

        user = fetch_one(get_db(), f"SELECT {USER_COLS} FROM users WHERE id = %s", (claims.get("sub"),))
        if user is None:
            raise Unauthorized("user no longer exists")

        if user.get("status") == "suspended":
            raise Forbidden("account is suspended")

        g.user = user
        return fn(*args, **kwargs)

    return wrapper


def require_permission(permission: str):
    """Guard a route with a shared permission (see ``shared/roles.py``)."""

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            role = getattr(g, "user", {}).get("role", "")
            if not _user_has(role, permission):
                raise Forbidden(f"permission '{permission}' is required")
            return fn(*args, **kwargs)

        return wrapper

    return decorator
