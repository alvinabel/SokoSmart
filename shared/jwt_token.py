"""JWT creation and verification shared by the Flask identity service and the
FastAPI marketplace API.

Single signing key (``JWT_SECRET``) means a token minted by ``backend`` can be
trusted by ``api`` without a second round trip. Access tokens are short lived;
refresh tokens carry a ``jti`` and are revocable (stored in Mongo).
"""

from __future__ import annotations

import time
import uuid
from typing import Any

import jwt as pyjwt

from .config import get_config


def now_ts() -> int:
    return int(time.time())


def _base_claims() -> dict[str, Any]:
    cfg = get_config()
    return {
        "iss": cfg.jwt_issuer,
        "aud": cfg.jwt_issuer,
        "iat": now_ts(),
    }


def create_access_token(user: dict[str, Any]) -> str:
    """Access token — carries identity + role, lives ~30 minutes."""
    cfg = get_config()
    claims = _base_claims()
    claims.update(
        {
            "sub": str(user["_id"]),
            "typ": "access",
            "exp": now_ts() + cfg.access_token_ttl_minutes * 60,
            "email": user.get("email"),
            "name": user.get("name"),
            "role": user.get("role", "buyer"),
        }
    )
    return pyjwt.encode(claims, cfg.jwt_secret, algorithm=cfg.jwt_algorithm)


def create_refresh_token(user_id: str) -> tuple[str, str]:
    """Refresh token — long lived, returns ``(token, jti)`` so servers can revoke it."""
    cfg = get_config()
    jti = uuid.uuid4().hex
    claims = _base_claims()
    claims.update(
        {
            "sub": str(user_id),
            "typ": "refresh",
            "jti": jti,
            "exp": now_ts() + cfg.refresh_token_ttl_days * 24 * 3600,
        }
    )
    token = pyjwt.encode(claims, cfg.jwt_secret, algorithm=cfg.jwt_algorithm)
    return token, jti


def decode_token(token: str, expected_type: str | None = None) -> dict[str, Any]:
    """Decode and verify a token. Raises ``jwt.PyJWTError`` on failure.

    Pass ``expected_type="access"`` / ``"refresh"`` to also enforce the token type.
    """
    cfg = get_config()
    claims = pyjwt.decode(
        token,
        cfg.jwt_secret,
        algorithms=[cfg.jwt_algorithm],
        issuer=cfg.jwt_issuer,
        audience=cfg.jwt_issuer,
    )
    if expected_type and claims.get("typ") != expected_type:
        raise pyjwt.InvalidTokenError(f"expected {expected_type} token")
    return claims