"""Bids routes."""

from fastapi import APIRouter, Depends, Query, status

from ..core.mongo import get_db
from ..dependencies import get_current_user, require_permission
from ..schemas import BidCreate
from ..schemas.bid import BidAction
from ..services import bids as svc

router = APIRouter(prefix="/bids", tags=["bids"])


@router.post("", status_code=status.HTTP_201_CREATED)
def create_bid(payload: BidCreate, user=Depends(require_permission("bid.create")), db=Depends(get_db)):
    return svc.create(db, user, payload.listing_id, payload.amount)


@router.get("/mine")
def my_bids(
    user=Depends(require_permission("bid.create")),
    db=Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
):
    return svc.list_mine(db, user, page=page, page_size=page_size)


@router.get("/listing/{listing_id}")
def bids_for_listing(listing_id: str, user=Depends(get_current_user), db=Depends(get_db)):
    return {"items": svc.list_for_listing(db, user, listing_id)}


@router.patch("/{bid_id}")
def respond_to_bid(bid_id: str, payload: BidAction, user=Depends(get_current_user), db=Depends(get_db)):
    return svc.respond(db, user, bid_id, payload.action)