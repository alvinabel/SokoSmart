"""Review payloads."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ReviewIn(BaseModel):
    listing_id: str
    rating: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=1000)