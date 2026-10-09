"""Authentication domain: register, login, refresh, logout, forgot-password."""

from .routes import auth_bp

__all__ = ["auth_bp"]