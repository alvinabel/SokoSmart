"""AgroBasket shared library.

Single source of truth for cross-service concerns:

- configuration (``config``), loaded from environment variables
- auth primitives (``jwt_token``, ``passwords``)
- role-based access control (``roles``)
- error types that map to HTTP responses (``errors``)
- canonical marketplace seed data (``categories``)
- a small PyMongo bootstrap (``mongo``)

Every service ``sys.path``-imports this package (see ``infra/seed_all.py`` for
the canonical wiring) so behaviour stays consistent across Flask and FastAPI.
"""

from .config import get_config, BaseConfig
from .roles import Role, PERMISSIONS, user_has, require_permission
from .errors import ApiError, Unauthorized, Forbidden, NotFound, Conflict, ValidationError

__all__ = [
    "get_config",
    "BaseConfig",
    "Role",
    "PERMISSIONS",
    "user_has",
    "require_permission",
    "ApiError",
    "Unauthorized",
    "Forbidden",
    "NotFound",
    "Conflict",
    "ValidationError",
]