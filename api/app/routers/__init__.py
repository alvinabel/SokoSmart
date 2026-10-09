"""API routers (one module per domain). Each is mounted under ``/api/v1``."""

from . import (  # noqa: F401
    bids,
    categories,
    favorites,
    listings,
    messages,
    notifications,
    orders,
    profile,
    reviews,
)

__all__ = [
    "bids",
    "categories",
    "favorites",
    "listings",
    "messages",
    "notifications",
    "orders",
    "profile",
    "reviews",
]