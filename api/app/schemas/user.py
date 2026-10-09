"""Profile / user payloads."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ProfileUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=80)
    phone: str | None = Field(default=None, max_length=30)
    bio: str | None = Field(default=None, max_length=500)
    location_city: str | None = Field(default=None, max_length=80)


class BecomeSeller(BaseModel):
    farm_name: str | None = Field(default=None, max_length=80)