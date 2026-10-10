"""Orders routes."""

from fastapi import APIRouter, Depends, Query, status

from ..core.mongo import get_db
from ..dependencies import require_permission
from ..schemas import OrderAction, OrderCreate
from ..services import orders as svc

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", status_code=status.HTTP_201_CREATED)
def create_order(payload: OrderCreate, user=Depends(require_permission("order.create")), db=Depends(get_db)):
    return svc.create(db, user, payload.listing_id, payload.quantity, payload.note or "")


@router.get("")
def list_orders(
    user=Depends(require_permission("order.read")),
    db=Depends(get_db),
    side: str = Query("buying", pattern="^(buying|selling)$"),
    status: str = "",
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
):
    return svc.list_orders(db, user, side=side, status=status, page=page, page_size=page_size)


@router.get("/{order_id}")
def get_order(order_id: str, user=Depends(require_permission("order.read")), db=Depends(get_db)):
    return svc.get(db, user, order_id)


@router.patch("/{order_id}")
def transition_order(
    order_id: str,
    payload: OrderAction,
    user=Depends(require_permission("order.update")),
    db=Depends(get_db),
):
    return svc.transition(db, user, order_id, payload.action)