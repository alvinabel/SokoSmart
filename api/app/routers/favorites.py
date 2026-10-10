"""Favorites routes."""

from fastapi import APIRouter, Depends, Query, Response, status

from ..core.db import get_db
from ..dependencies import require_permission
from ..services import favorites as svc

router = APIRouter(prefix="/favorites", tags=["favorites"])


@router.get("")
def list_favorites(
    user=Depends(require_permission("favorite.manage")),
    db=Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
):
    return svc.list_favorites(db, user, page=page, page_size=page_size)


@router.post("/{listing_id}")
def toggle_favorite(
    listing_id: str,
    user=Depends(require_permission("favorite.manage")),
    db=Depends(get_db),
):
    return svc.toggle(db, user, listing_id)


@router.delete("/{listing_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_favorite(
    listing_id: str,
    user=Depends(require_permission("favorite.manage")),
    db=Depends(get_db),
):
    svc.toggle(db, user, listing_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)