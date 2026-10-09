"""Shared schema utilities."""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class Location(BaseModel):
    city: str = Field(min_length=2, max_length=80)
    district: str | None = Field(default=None, max_length=80)


class Page(BaseModel, Generic[T]):
    """Standard pagination envelope returned by list endpoints."""

    items: list[T]
    total: int
    page: int
    page_size: int
    pages: int


class Meta(BaseModel):
    service: str
    version: str
    docs: str


def page_dict(items: list[Any], total: int, page: int, page_size: int) -> dict:
    pages = (total + page_size - 1) // page_size if page_size else 1
    return {"items": items, "total": total, "page": page, "page_size": page_size, "pages": max(pages, 1)}