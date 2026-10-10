"""Notifications routes."""

from fastapi import APIRouter, Depends, Query, Response, status

from ..core.db import get_db
from ..dependencies import get_current_user
from ..services import notifications as svc

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("")
def list_notifications(
    user=Depends(get_current_user),
    db=Depends(get_db),
    unread_only: bool = False,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
):
    return svc.list_notifications(db, user, unread_only=unread_only, page=page, page_size=page_size)


@router.get("/unread-count")
def unread_count(user=Depends(get_current_user), db=Depends(get_db)):
    return {"count": svc.unread_count(db, user)}


@router.patch("/read-all")
def mark_all_read(user=Depends(get_current_user), db=Depends(get_db)):
    return svc.mark_all_read(db, user)


@router.patch("/{notification_id}")
def mark_read(notification_id: str, user=Depends(get_current_user), db=Depends(get_db)):
    return svc.mark_read(db, user, notification_id)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def clear_read(user=Depends(get_current_user), db=Depends(get_db)):
    svc.clear_read(db, user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)