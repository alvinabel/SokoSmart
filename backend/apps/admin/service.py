"""Admin business logic (dashboard stats, moderation, audit logging).

Reads/writes the same PostgreSQL tables the FastAPI marketplace service uses, so
moderation actions here are immediately visible to the storefront.
"""

from __future__ import annotations

from datetime import datetime, timezone

from psycopg.types.json import Json

from shared.categories import CATEGORIES
from shared.db import execute, fetch_all, fetch_one, insert_returning
from shared.errors import Conflict, NotFound, ValidationError
from shared.roles import Role

LISTING_MODERATION_STATUS = {
    "approve": "active",
    "reject": "rejected",
    "suspend": "suspended",
    "activate": "active",
}

LISTING_COLS = (
    "l.id AS _id, l.title, l.category, l.price, l.unit, l.quantity, l.status, "
    "l.views, l.location, l.created_at, u.name AS seller_name"
)


def now() -> datetime:
    return datetime.now(timezone.utc)


def audit(db, actor: dict, action: str, target: dict | None = None, meta: dict | None = None) -> None:
    insert_returning(
        db,
        "INSERT INTO audit_logs (actor, actor_email, action, target, meta, created_at) "
        "VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
        (
            str(actor.get("_id")) if actor else None,
            actor.get("email") if actor else None,
            action,
            Json(target or {}),
            Json(meta or {}),
            now(),
        ),
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
    role_rows = fetch_all(db, "SELECT role, count(*) AS n FROM users GROUP BY role")
    by_role = {role: 0 for role in Role.ALL}
    by_role.update({r["role"]: r["n"] for r in role_rows})

    listing_status_counts = {
        r["status"]: r["n"]
        for r in fetch_all(db, "SELECT status, count(*) AS n FROM listings GROUP BY status")
    }
    category_counts = {
        r["category"]: r["n"]
        for r in fetch_all(db, "SELECT category, count(*) AS n FROM listings GROUP BY category")
    }
    order_status_counts = {
        r["status"]: r["n"]
        for r in fetch_all(db, "SELECT status, count(*) AS n FROM orders GROUP BY status")
    }
    revenue = fetch_one(
        db, "SELECT COALESCE(sum(total), 0) AS total FROM orders WHERE status = 'completed'"
    )["total"]

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
        for u in fetch_all(
            db,
            "SELECT id AS _id, name, email, role, status, created_at FROM users ORDER BY created_at DESC LIMIT 5",
        )
    ]

    recent_listings = [
        serialize_listing(doc)
        for doc in fetch_all(
            db,
            f"SELECT {LISTING_COLS} FROM listings l LEFT JOIN users u ON u.id = l.seller_id "
            "ORDER BY l.created_at DESC LIMIT 8",
        )
    ]

    return {
        "users": {
            "total": fetch_one(db, "SELECT count(*) AS n FROM users")["n"],
            "by_role": by_role,
            "active": fetch_one(db, "SELECT count(*) AS n FROM users WHERE status <> 'suspended'")["n"],
            "suspended": fetch_one(db, "SELECT count(*) AS n FROM users WHERE status = 'suspended'")["n"],
        },
        "listings": {
            "total": fetch_one(db, "SELECT count(*) AS n FROM listings")["n"],
            "by_status": listing_status_counts,
            "by_category": by_category,
        },
        "orders": {
            "total": fetch_one(db, "SELECT count(*) AS n FROM orders")["n"],
            "by_status": order_status_counts,
        },
        "revenue": round(float(revenue or 0), 2),
        "recent_users": recent_users,
        "recent_activity": recent_listings,
    }


# --------------------------------------------------------------------------- #
# Users
# --------------------------------------------------------------------------- #
def list_users(db, q: str = "", role: str = "", page: int = 1, page_size: int = 20) -> dict:
    where: list[str] = []
    params: list = []
    if role:
        where.append("role = %s")
        params.append(role)
    if q:
        where.append("(name ILIKE %s OR email ILIKE %s)")
        like = f"%{q}%"
        params.extend([like, like])
    clause = ("WHERE " + " AND ".join(where)) if where else ""

    total = fetch_one(db, f"SELECT count(*) AS n FROM users {clause}", tuple(params))["n"]
    rows = fetch_all(
        db,
        "SELECT id AS _id, name, email, role, status, created_at FROM users "
        f"{clause} ORDER BY created_at DESC LIMIT %s OFFSET %s",
        tuple(params) + (page_size, (page - 1) * page_size),
    )
    items = [
        {
            "id": str(u["_id"]),
            "name": u.get("name", ""),
            "email": u.get("email", ""),
            "role": u.get("role", "buyer"),
            "status": u.get("status", "active"),
            "created_at": u.get("created_at").isoformat() if u.get("created_at") else None,
        }
        for u in rows
    ]
    return _paged(items, total, page, page_size)


def _active_admin_count(db, exclude_id: str | None = None) -> int:
    sql = "SELECT count(*) AS n FROM users WHERE role = %s AND status <> 'suspended'"
    params: list = [Role.ADMIN]
    if exclude_id is not None:
        sql += " AND id <> %s"
        params.append(exclude_id)
    return fetch_one(db, sql, tuple(params))["n"]


def update_user(db, user_id: str, action: str, value: str | None, actor: dict) -> dict:
    user = fetch_one(db, "SELECT id AS _id, role, email FROM users WHERE id = %s", (user_id,))
    if user is None:
        raise NotFound("user not found")

    if action == "suspend":
        if user.get("role") == Role.ADMIN and _active_admin_count(db, user_id) == 0:
            raise Conflict("cannot suspend the last active admin")
        update = {"status": "suspended", "updated_at": now()}
    elif action == "activate":
        update = {"status": "active", "updated_at": now()}
    elif action == "role":
        if value not in Role.ALL:
            raise ValidationError("invalid role")
        if user.get("role") == Role.ADMIN and value != Role.ADMIN and _active_admin_count(db, user_id) == 0:
            raise Conflict("cannot demote the last active admin")
        update = {"role": value, "updated_at": now()}
    else:
        raise ValidationError(f"unsupported action '{action}'")

    sets = ", ".join(f"{k} = %s" for k in update)
    execute(db, f"UPDATE users SET {sets} WHERE id = %s", tuple(update.values()) + (user_id,))
    audit(db, actor, f"user.{action}", {"user_id": user_id, "email": user.get("email")}, {"value": value})
    return {"id": user_id, **update}


def delete_user(db, user_id: str, actor: dict) -> None:
    user = fetch_one(db, "SELECT id AS _id, role, email FROM users WHERE id = %s", (user_id,))
    if user is None:
        raise NotFound("user not found")
    if user.get("role") == Role.ADMIN and _active_admin_count(db, user_id) == 0:
        raise Conflict("cannot delete the last active admin")
    execute(db, "DELETE FROM users WHERE id = %s", (user_id,))
    audit(db, actor, "user.delete", {"user_id": user_id, "email": user.get("email")})


# --------------------------------------------------------------------------- #
# Listings
# --------------------------------------------------------------------------- #
def list_listings(db, q: str = "", status: str = "", page: int = 1, page_size: int = 20) -> dict:
    where: list[str] = []
    params: list = []
    if status:
        where.append("l.status = %s")
        params.append(status)
    else:
        where.append("l.status <> 'deleted'")
    if q:
        where.append("(l.title ILIKE %s OR l.description ILIKE %s)")
        like = f"%{q}%"
        params.extend([like, like])
    clause = "WHERE " + " AND ".join(where)

    total = fetch_one(db, f"SELECT count(*) AS n FROM listings l {clause}", tuple(params))["n"]
    rows = fetch_all(
        db,
        f"SELECT {LISTING_COLS} FROM listings l LEFT JOIN users u ON u.id = l.seller_id "
        f"{clause} ORDER BY l.created_at DESC LIMIT %s OFFSET %s",
        tuple(params) + (page_size, (page - 1) * page_size),
    )
    items = [serialize_listing(doc) for doc in rows]
    return _paged(items, total, page, page_size)


def moderate_listing(db, listing_id: str, action: str, actor: dict) -> dict:
    if action not in LISTING_MODERATION_STATUS:
        raise ValidationError(f"unsupported action '{action}'")
    listing = fetch_one(db, "SELECT id AS _id FROM listings WHERE id = %s", (listing_id,))
    if listing is None:
        raise NotFound("listing not found")

    status = LISTING_MODERATION_STATUS[action]
    execute(
        db,
        "UPDATE listings SET status = %s, moderated_at = %s, moderated_by = %s WHERE id = %s",
        (status, now(), str(actor.get("_id")), listing_id),
    )
    audit(db, actor, f"listing.{action}", {"listing_id": listing_id}, {"status": status})
    return {"id": listing_id, "status": status}


def list_audit_logs(db, limit: int = 30) -> list[dict]:
    rows = fetch_all(
        db,
        "SELECT id AS _id, actor_email, action, target, meta, created_at FROM audit_logs "
        "ORDER BY created_at DESC LIMIT %s",
        (limit,),
    )
    return [
        {
            "id": str(doc["_id"]),
            "actor_email": doc.get("actor_email"),
            "action": doc.get("action"),
            "target": doc.get("target", {}),
            "meta": doc.get("meta", {}),
            "created_at": doc.get("created_at").isoformat() if doc.get("created_at") else None,
        }
        for doc in rows
    ]
