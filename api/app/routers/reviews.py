"""Reviews routes."""

from fastapi import APIRouter, Depends, Query, Response, status

from ..core.db import get_db
from ..dependencies import get_current_user, require_permission
from ..schemas import ReviewIn
from ..services import reviews as svc

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.post("", status_code=status.HTTP_201_CREATED)
def create_review(payload: ReviewIn, user=Depends(require_permission("review.create")), db=Depends(get_db)):
    return svc.create(db, user, payload.listing_id, payload.rating, payload.comment)


@router.get("/listing/{listing_id}")
def reviews_for_listing(
    listing_id: str,
    db=Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
):
    return svc.list_for_listing(db, listing_id, page=page, page_size=page_size)


@router.get("/seller/{seller_id}")
def seller_reviews(
    seller_id: str,
    db=Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
):
    return svc.seller_summary(db, seller_id, page=page, page_size=page_size)


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review(review_id: str, user=Depends(get_current_user), db=Depends(get_db)):
    svc.delete(db, user, review_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)