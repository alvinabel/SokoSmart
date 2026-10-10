"""Application factory: wires config, CORS, blueprints, PostgreSQL schema and error handlers."""

import logging

from flask import Flask, jsonify, request
from flask_cors import CORS

from shared import ApiError, get_config
from shared.db import get_conn
from shared.schema import ensure_schema

from .admin.routes import admin_bp
from .auth.routes import auth_bp
from .common.db import release_db

logger = logging.getLogger("agrobasket.backend")


def create_app() -> Flask:
    cfg = get_config()

    app = Flask("agrobasket-backend")
    app.config["JSON_SORT_KEYS"] = False

    # CORS — locked to configured frontend origins (+ localhost for dev).
    CORS(
        app,
        origins=cfg.cors_origins,
        supports_credentials=True,
        allow_headers=["Content-Type", "Authorization"],
        expose_headers=["X-Total-Count"],
    )

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)

    @app.get("/api/health")
    def health():
        with get_conn() as db:
            db.execute("SELECT 1")
        return jsonify(
            {"status": "ok", "service": "agrobasket-backend", "version": "1.0.0", "env": cfg.app_env}
        )

    @app.errorhandler(ApiError)
    def handle_api_error(err: ApiError):
        return jsonify(err.to_dict()), err.status_code

    @app.errorhandler(404)
    def handle_404(_err):
        return jsonify({"error": {"code": "not_found", "message": "resource not found"}}), 404

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        logger.exception("unhandled error on %s", request.path)
        return jsonify({"error": {"code": "internal_error", "message": "server error"}}), 500

    @app.teardown_request
    def _teardown(_exc):
        release_db()

    _bootstrap_schema()
    return app


def _bootstrap_schema() -> None:
    """Apply DDL (best-effort) so a fresh database is usable on first boot."""
    try:
        with get_conn() as conn:
            ensure_schema(conn)
    except Exception:  # pragma: no cover - defensive
        logger.warning("could not ensure Postgres schema on boot")
