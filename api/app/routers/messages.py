"""Messages routes (REST inbox + thread; WebSocket upgrade path documented in docs/)."""

from fastapi import APIRouter, Depends, Query, status

from ..core.mongo import get_db
from ..dependencies import require_permission
from ..schemas import MessageSend
from ..services import messages as svc

router = APIRouter(prefix="/messages", tags=["messages"])


@router.get("")
def inbox(user=Depends(require_permission("message.send")), db=Depends(get_db)):
    return svc.inbox(db, user)


@router.get("/{user_id}")
def thread(
    user_id: str,
    user=Depends(require_permission("message.send")),
    db=Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    return svc.thread(db, user, user_id, page=page, page_size=page_size)


@router.post("/{user_id}", status_code=status.HTTP_201_CREATED)
def send(
    user_id: str,
    payload: MessageSend,
    user=Depends(require_permission("message.send")),
    db=Depends(get_db),
):
    return svc.send(db, user, user_id, payload.body, payload.listing_id)