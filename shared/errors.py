"""Domain error types that serialize to a consistent HTTP JSON body:

    {"error": {"code": "listing_not_found", "message": "..."}}
"""

from __future__ import annotations

from typing import Any


class ApiError(Exception):
    status_code = 500
    code = "internal_error"

    def __init__(self, message: str = "", *, code: str | None = None, **context: Any) -> None:
        super().__init__(message)
        self.message = message or self.code.replace("_", " ")
        self.code = code or self.code
        self.context = context

    def to_dict(self) -> dict[str, Any]:
        return {"error": {"code": self.code, "message": self.message, **self.context}}


class Unauthorized(ApiError):
    status_code = 401
    code = "unauthorized"


class Forbidden(ApiError):
    status_code = 403
    code = "forbidden"


class NotFound(ApiError):
    status_code = 404
    code = "not_found"


class Conflict(ApiError):
    status_code = 409
    code = "conflict"


class ValidationError(ApiError):
    status_code = 422
    code = "validation_error"