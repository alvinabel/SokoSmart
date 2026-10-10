"""HTTP layer for authentication."""

from flask import Blueprint, g, jsonify, request

from pydantic import ValidationError as PydanticValidationError

from shared.errors import ValidationError
from shared.mongo import get_db

from ..common.decorators import jwt_required
from . import service
from .schemas import ForgotIn, LoginIn, RefreshIn, RegisterIn

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def _body(model, raw: dict):
    try:
        return model.model_validate(raw)
    except PydanticValidationError as exc:
        raise ValidationError("request body is invalid", details=exc.errors()) from exc


@auth_bp.post("/register")
def register():
    payload = _body(RegisterIn, request.get_json(silent=True) or {})
    result = service.register(payload.model_dump(), get_db())
    return jsonify(result), 201


@auth_bp.post("/login")
def login():
    payload = _body(LoginIn, request.get_json(silent=True) or {})
    result = service.login(payload.email, payload.password, get_db())
    return jsonify(result), 200


@auth_bp.post("/refresh")
def refresh():
    payload = _body(RefreshIn, request.get_json(silent=True) or {})
    result = service.refresh(payload.refresh_token, get_db())
    return jsonify(result), 200


@auth_bp.post("/logout")
@jwt_required
def logout():
    payload = request.get_json(silent=True) or {}
    service.logout(g.user, payload.get("refresh_token", ""), get_db())
    return ("", 204)


@auth_bp.get("/me")
@jwt_required
def me():
    return jsonify({"user": service.serialize_user(g.user)}), 200


@auth_bp.post("/forgot-password")
def forgot_password():
    _body(ForgotIn, request.get_json(silent=True) or {})
    # Scaffold: dispatch an email/password-reset job here (Resend/Twilio SendGrid).
    return ("", 204)