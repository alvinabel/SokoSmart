"""Service layer — business logic for the marketplace API.

Each module owns one domain and talks to Mongo collections through ``COLLECTIONS``.
HTTP concerns (auth, validation, status codes) stay in ``routers``.
"""

from . import (  # noqa: F401  (imports register submodules, reuse is via routers)
    bids,
    categories,
    favorites,
    listings,
    messages,
    notifications,
    orders,
    profile,
    reviews,
    serializers,
)