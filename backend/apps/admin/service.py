"""Admin business logic (dashboard stats, moderation, audit logging).

Reads/writes the same Mongo collections the FastAPI marketplace service uses, so
moderation actions here are immediately visible to the storefront.
"""

from __future__ import annotations

from datetime import datetime, timezone

from bson import ObjectId

from shared.categories import CATEGORIES
from shared.errors import Conflict, NotFound, ValidationError
from shared.mongo import COLLECTIONS
from shared.roles import Role

LISTING_MODERATION_STATUS = {
    "approve": "active",
    "reject": "rejected",
    "suspend": "suspended",
    "activate": "active",
}


def now() -> datetime:
    return datetime.now(timezone.utc)


def audit(db, actor: dict, action: str, target: dict | None = None, meta: dict | None = None) -> None:
    db[COLLECTIONS["audit_logs"]].insert_one(
        {
            "actor": str(actor.get("_id")) if actor else None,
            "actor_email": actor.get("email") if actor else None,
            "action": action,
            "target": target or {},
            "meta": meta or {},
            "created_at": now(),
        }
    )


# --------------------------------------------------------------------------- #
# Serialization helpers
# --------------------------------------------------------------------------- #
def serialize_listing(listing: dict) -> dict:
    return {
        "id": str(listing["_id"]),
        "title": listing.get("title", ""),
        "category": listing.get("category", ""),
        "price": listing.get("price", 0),
        "unit": listing.get("unit", "unit"),
        "quantity": listing.get("quantity", 0),
        "status": listing.get("status", "active"),
        "views": listing.get("views", 0),
        "city": (listing.get("location") or {}).get("city", ""),
        "seller": listing.get("seller_name", ""),
        "created_at": listing.get("created_at").isoformat() if listing.get("created_at") else None,
    }


def _paged(items, total, page, page_size) -> dict:
    pages = (total + page_size - 1) // page_size if page_size else 1
    return {"items": items, "total": total, "page": page, "page_size": page_size, "pages": max(pages, 1)}


# --------------------------------------------------------------------------- #
# Dashboard
# --------------------------------------------------------------------------- #
def dashboard_stats(db) -> dict:
    users = db[COLLECTIONS["users"]]
    listings = db[COLLECTIONS["listings"]]
    orders = db[COLLECTIONS["orders"]]

    by_role = {role: users.count_documents({"role": role}) for role in Role.ALL}

    listing_status_counts: dict[str, int] = {}
    category_counts: dict[str, int] = {}
    for doc in listings.find({}, {"status": 1, "category": 1}):
        status = doc.get("status", "active")
        listing_status_counts[status] = listing_status_counts.get(status, 0) + 1
        cat = doc.get("category", "uncategorized")
        category_counts[cat] = category_counts.get(cat, 0) + 1

    order_status_counts: dict[str, int] = {}
    revenue = 0.0
    for doc in orders.find({}, {"status": 1, "total": 1}):
        status = doc.get("status", "placed")
        order_status_counts[status] = order_status_counts.get(status, 0) + 1
        if status == "completed":
            revenue += float(doc.get("total", 0) or 0)

    cat_name = {c["slug"]: c for c in CATEGORIES}
    by_category = [
        {
            "slug": slug,
            "name": cat_name.get(slug, {}).get("name", slug.title()),
            "color": cat_name.get(slug, {}).get("color", "#4CAF50"),
            "count": count,
        }
        for slug, count in sorted(category_counts.items(), key=lambda kv: kv[1], reverse=True)
    ]

    recent_users = [
        {
            "id": str(u["_id"]),
            "name": u.get("name", ""),
            "email": u.get("email", ""),
            "role": u.get("role", "buyer"),
            "status": u.get("status", "active"),
            "created_at": u.get("created_at").isoformat() if u.get("created_at") else None,
        }
        for u in users.find().sort("created_at", -1).limit(5)
    ]

    recent_listings = [
        serialize_listing(doc) for doc in listings.find().sort("created_at", -1).limit(8)
    ]

    return {
        "users": {
            "total": users.count_documents({}),
            "by_role": by_role,
            "active": users.count_documents({"status": {"$ne": "suspended"}}),
            "suspended": users.count_documents({"status": "suspended"}),
        },
        "listings": {
            "total": listings.count_documents({}),
            "by_status": listing_status_counts,
            "by_category": by_category,
        },
        "orders": {"total": orders.count_documents({}), "by_status": order_status_counts},
        "revenue": round(revenue, 2),
        "recent_users": recent_users,
        "recent_activity": recent_listings,
    }


# --------------------------------------------------------------------------- #
# Users
# --------------------------------------------------------------------------- #
def list_users(db, q: str = "", role: str = "", page: int = 1, page_size: int = 20) -> dict:
    query: dict = {}
    if role:
        query["role"] = role
    if q:
        query["$or"] = [
            {"name": {"$regex": q, "$options": "i"}},
            {"email": {"$regex": q, "$options": "i"}},
        ]
    coll = db[COLLECTIONS["users"]]
    total = coll.count_documents(query)
    cursor = coll.find(query).sort("created_at", -1).skip((page - 1) * page_size).limit(page_size)
    items = [
        {
            "id": str(u["_id"]),
            "name": u.get("name", ""),
            "email": u.get("email", ""),
            "role": u.get("role", "buyer"),
            "status": u.get("status", "active"),
            "created_at": u.get("created_at").isoformat() if u.get("created_at") else None,
        }
        for u in cursor
    ]
    return _paged(items, total, page, page_size)


def _active_admin_count(db, exclude_id: ObjectId | None = None) -> int:
    query = {"role": Role.ADMIN, "status": {"$ne": "suspended"}}
    if exclude_id is not None:
        query["_id"] = {"$ne": exclude_id}
    return db[COLLECTIONS["users"]].count_documents(query)


def update_user(db, user_id: str, action: str, value: str | None, actor: dict) -> dict:
    try:
        oid = ObjectId(user_id)
    except Exception as exc:
        raise NotFound("user not found") from exc
    user = db[COLLECTIONS["users"]].find_one({"_id": oid})
    if user is None:
        raise NotFound("user not found")

    if action == "suspend":
        if user.get("role") == Role.ADMIN and _active_admin_count(db, oid) == 0:
            raise Conflict("cannot suspend the last active admin")
        update = {"status": "suspended", "updated_at": now()}
    elif action == "activate":
        update = {"status": "active", "updated_at": now()}
    elif action == "role":
        if value not in Role.ALL:
            raise ValidationError("invalid role")
        if user.get("role") == Role.ADMIN and value != Role.ADMIN and _active_admin_count(db, oid) == 0:
            raise Conflict("cannot demote the last active admin")
        update = {"role": value, "updated_at": now()}
    else:
        raise ValidationError(f"unsupported action '{action}'")

    db[COLLECTIONS["users"]].update_one({"_id": oid}, {"$set": update})
    audit(db, actor, f"user.{action}", {"user_id": user_id, "email": user.get("email")}, {"value": value})
    return {"id": user_id, **update}


def delete_user(db, user_id: str, actor: dict) -> None:
    try:
        oid = ObjectId(user_id)
    except Exception as exc:
        raise NotFound("user not found") from exc
    user = db[COLLECTIONS["users"]].find_one({"_id": oid})
    if user is None:
        raise NotFound("user not found")
    if user.get("role") == Role.ADMIN and _active_admin_count(db, oid) == 0:
        raise Conflict("cannot delete the last active admin")
    db[COLLECTIONS["users"]].delete_one({"_id": oid})
    audit(db, actor, "user.delete", {"user_id": user_id, "email": user.get("email")})


# --------------------------------------------------------------------------- #
# Listings
# --------------------------------------------------------------------------- #
def list_listings(db, q: str = "", status: str = "", page: int = 1, page_size: int = 20) -> dict:
    query: dict = {}
    if status:
        query["status"] = status
    else:
        query["status"] = {"$ne": "deleted"}
    if q:
        query["$or"] = [
            {"title": {"$regex": q, "$options": "i"}},
            {"description": {"$regex": q, "$options": "i"}},
        ]
    coll = db[COLLECTIONS["listings"]]
    total = coll.count_documents(query)
    cursor = coll.find(query).sort("created_at", -1).skip((page - 1) * page_size).limit(page_size)
    items = [serialize_listing(doc) for doc in cursor]
    return _paged(items, total, page, page_size)


def moderate_listing(db, listing_id: str, action: str, actor: dict) -> dict:
    if action not in LISTING_MODERATION_STATUS:
        raise ValidationError(f"unsupported action '{action}'")
    try:
        oid = ObjectId(listing_id)
    except Exception as exc:
        raise NotFound("listing not found") from exc
    listing = db[COLLECTIONS["listings"]].find_one({"_id": oid})
    if listing is None:
        raise NotFound("listing not found")

    status = LISTING_MODERATION_STATUS[action]
    db[COLLECTIONS["listings"]].update_one(
        {"_id": oid},
        {"$set": {"status": status, "moderated_at": now(), "moderated_by": str(actor.get("_id"))}},
    )
    audit(db, actor, f"listing.{action}", {"listing_id": listing_id}, {"status": status})
    return {"id": listing_id, "status": status}


def list_audit_logs(db, limit: int = 30) -> list[dict]:
    cursor = db[COLLECTIONS["audit_logs"]].find().sort("created_at", -1).limit(limit)
    return [
        {
            "id": str(doc["_id"]),
            "actor_email": doc.get("actor_email"),
            "action": doc.get("action"),
            "target": doc.get("target", {}),
            "meta": doc.get("meta", {}),
            "created_at": doc.get("created_at").isoformat() if doc.get("created_at") else None,
        }
        for doc in cursor
    ]