"""Listing payloads."""

from __future__ import annotations

from pydantic import BaseModel, Field

from .common import Location


class ListingCreate(BaseModel):
    title: str = Field(min_length=3, max_length=120)
    description: str = Field(default="", max_length=5000)
    category: str = Field(min_length=2, max_length=40)
    price: float = Field(gt=0)
    unit: str = Field(default="unit", max_length=20, description="kg, crate, head, sack…")
    quantity: float = Field(gt=0, le=1_000_000)
    quality: str | None = Field(default=None, max_length=120)
    location: Location
    images: list[str] = Field(default_factory=list, max_length=8)


class ListingUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=120)
    description: str | None = Field(default=None, max_length=5000)
    category: str | None = Field(default=None, min_length=2, max_length=40)
    price: float | None = Field(default=None, gt=0)
    unit: str | None = Field(default=None, max_length=20)
    quantity: float | None = Field(default=None, gt=0, le=1_000_000)
    quality: str | None = Field(default=None, max_length=120)
    location: Location | None = None
    images: list[str] | None = Field(default=None, max_length=8)
    status: str | None = Field(default=None, description="owner actions: sold | active")