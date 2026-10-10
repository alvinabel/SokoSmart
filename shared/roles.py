"""Role-based access control (RBAC).

AgroBasket uses a small, flat permission matrix:

    buyer     -> can browse, favorite, bid, order, review, message
    seller    -> buyer capabilities + can manage own listings, orders, bids
    moderator -> can moderate listings, users; read stats
    admin     -> everything (including role assignment, deletion)

Permissions are enforced at the API layer by:

- ``backend`` Flask:    ``@require_permission("listing.manage")`` decorators
- ``api`` FastAPI:      ``require_permission(...)`` dependencies

The UI also hides features behind ``useAuth().can(<permission>)``.
"""

from __future__ import annotations


class Role:
    BUYER = "buyer"
    SELLER = "seller"
    MODERATOR = "moderator"
    ADMIN = "admin"

    ALL = (BUYER, SELLER, MODERATOR, ADMIN)

    @classmethod
    def is_valid(cls, value: str) -> bool:
        return value in cls.ALL


# ---- Permission vocabulary (keep sorted) ---------------------------------
P_BUYER_BASE = (
    "profile.read",
    "profile.update",
    "listing.read",
    "favorite.manage",
    "message.send",
    "notification.read",
)


PERMISSIONS: dict[str, tuple[str, ...]] = {
    Role.BUYER: P_BUYER_BASE + ("order.create", "order.read", "review.create", "bid.create"),
    Role.SELLER: P_BUYER_BASE
    + (
        "order.create",
        "order.read",
        "order.update",
        "review.create",
        "listing.manage",
        "bid.create",
        "bid.respond",
        "listing.sold",
    ),
    Role.MODERATOR: P_BUYER_BASE
    + (
        "order.create",
        "order.read",
        "order.update",
        "review.create",
        "bid.create",
        "bid.respond",
        "listing.manage",
        "listing.moderate",
        "user.read",
        "user.moderate",
        "stats.read",
        "category.manage",
    ),
    Role.ADMIN: tuple(
        sorted(
            set(P_BUYER_BASE)
            | {
                "order.create",
                "order.read",
                "order.update",
                "review.create",
                "review.moderate",
                "listing.manage",
                "listing.moderate",
                "bid.create",
                "bid.respond",
                "user.read",
                "user.moderate",
                "user.roles",
                "category.manage",
                "stats.read",
                "notifications.send",
            }
        )
    ),
}


def user_has(role: str | None, permission: str) -> bool:
    """True if ``role`` grants ``permission``."""
    return permission in PERMISSIONS.get(role or "", ())


def require_permission(role: str | None, permission: str) -> bool:
    """Same as :func:`user_has` but raises if permission is missing."""
    if not user_has(role, permission):
        from .errors import Forbidden

        raise Forbidden(f"permission '{permission}' is required")
    return True