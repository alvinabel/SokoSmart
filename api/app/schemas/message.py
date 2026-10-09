"""Message payloads."""

from __future__ import annotations

from pydantic import BaseModel, Field


class MessageSend(BaseModel):
    body: str = Field(min_length=1, max_length=2000)
    listing_id: str | None = Field(default=None, description="context listing, if any")