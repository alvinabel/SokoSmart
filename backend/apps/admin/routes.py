"""HTTP layer for the admin dashboard + moderation endpoints."""

from flask import Blueprint, g, jsonify, request

from shared.errors import Forbidden
from shared.roles import user_has

from ..common.db import get_db
from ..common.decorators import jwt_required, require_permission
from . import service

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")


def _int(name: str, default: int) -> int:
    try:
        return max(int(request.args.get(name, default)), 1)
    except (TypeError, ValueError):
        return default


@admin_bp.get("/dashboard/stats")
@jwt_required
@require_permission("stats.read")
def dashboard_stats():
    return jsonify(service.dashboard_stats(get_db())), 200


@admin_bp.get("/users")
@jwt_required
@require_permission("user.read")
def list_users():
    data = service.list_users(
        get_db(),
        q=request.args.get("q", ""),
        role=request.args.get("role", ""),
        page=_int("page", 1),
        page_size=min(_int("page_size", 20), 100),
    )
    return jsonify(data), 200


@admin_bp.patch("/users/<user_id>")
@jwt_required
@require_permission("user.moderate")
def update_user(user_id: str):
    body = request.get_json(silent=True) or {}
    action = body.get("action", "")
    if action == "role" and not user_has(g.user.get("role"), "user.roles"):
        raise Forbidden("only admins may assign roles")
    result = service.update_user(get_db(), user_id, action, body.get("value"), g.user)
    return jsonify(result), 200


@admin_bp.delete("/users/<user_id>")
@jwt_required
@require_permission("user.roles")
def delete_user(user_id: str):
    service.delete_user(get_db(), user_id, g.user)
    return ("", 204)


@admin_bp.get("/listings")
@jwt_required
@require_permission("listing.moderate")
def list_listings():
    data = service.list_listings(
        get_db(),
        q=request.args.get("q", ""),
        status=request.args.get("status", ""),
        page=_int("page", 1),
        page_size=min(_int("page_size", 20), 100),
    )
    return jsonify(data), 200


@admin_bp.patch("/listings/<listing_id>")
@jwt_required
@require_permission("listing.moderate")
def moderate_listing(listing_id: str):
    body = request.get_json(silent=True) or {}
    result = service.moderate_listing(get_db(), listing_id, body.get("action", ""), g.user)
    return jsonify(result), 200


@admin_bp.get("/audit-logs")
@jwt_required
@require_permission("stats.read")
def audit_logs():
    limit = min(_int("limit", 30), 200)
    return jsonify({"items": service.list_audit_logs(get_db(), limit)}), 200