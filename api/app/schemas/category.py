"""Category payloads."""

from __future__ import annotations

from pydantic import BaseModel, Field


class CategoryCreate(BaseModel):
    slug: str = Field(min_length=2, max_length=40, pattern=r"^[a-z0-9-]+$")
    name: str = Field(min_length=2, max_length=60)
    emoji: str = Field(default="🥬", max_length=8)
    color: str = Field(default="#4CAF50", max_length=9)


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=60)
    emoji: str | None = Field(default=None, max_length=8)
    color: str | None = Field(default=None, max_length=9)