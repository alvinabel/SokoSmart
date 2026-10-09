"""Environment-driven configuration shared by every service."""

import os
from functools import lru_cache


def _env(key: str, default: str = "") -> str:
    value = os.getenv(key, default)
    return (value or "").strip()


class BaseConfig:
    """Loads configuration from environment variables (or sane dev defaults)."""

    def __init__(self) -> None:
        self.app_env = _env("APP_ENV", "development")
        self.debug = self.app_env != "production"

        self.mongo_uri = _env("MONGO_URI", "mongodb://localhost:27017/agrobasket")
        self.mongo_db = _env("MONGO_DB", "agrobasket")

        self.jwt_secret = _env("JWT_SECRET", "dev-insecure-secret-change-me")
        self.jwt_algorithm = _env("JWT_ALGORITHM", "HS256")
        self.jwt_issuer = _env("JWT_ISSUER", "agrobasket")
        self.access_token_ttl_minutes = int(_env("ACCESS_TOKEN_TTL_MINUTES", "30"))
        self.refresh_token_ttl_days = int(_env("REFRESH_TOKEN_TTL_DAYS", "7"))

        raw_origins = _env("CORS_ORIGINS", "http://localhost:5173")
        self.cors_origins = [o.strip() for o in raw_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    def warn_if_insecure(self) -> str | None:
        if self.jwt_secret in ("dev-insecure-secret-change-me", "change-me-in-production"):
            return (
                "JWT_SECRET is still the development default. "
                "Set a long random value before deploying."
            )
        return None


@lru_cache
def get_config() -> BaseConfig:
    """Cached config instance (module-level singleton via functools)."""
    return BaseConfig()