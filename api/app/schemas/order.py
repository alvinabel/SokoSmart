"""Order payloads."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class OrderCreate(BaseModel):
    listing_id: str
    quantity: float = Field(gt=0, le=1_000_000)
    note: str | None = Field(default=None, max_length=500)


class OrderAction(BaseModel):
    action: Literal["accept", "reject", "fulfill", "complete", "cancel"]