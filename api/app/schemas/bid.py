"""Bid payloads."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class BidCreate(BaseModel):
    listing_id: str
    amount: float = Field(gt=0)


class BidAction(BaseModel):
    action: Literal["accept", "decline"]