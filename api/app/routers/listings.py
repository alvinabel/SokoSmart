"""Listings routes."""

from fastapi import APIRouter, Depends, Query, Response, status

from ..core.mongo import get_db
from ..dependencies import get_current_user, require_permission
from ..schemas import ListingCreate, ListingUpdate
from ..services import listings as svc

router = APIRouter(prefix="/listings", tags=["listings"])


@router.get("")
def list_listings(
    db=Depends(get_db),
    q: str = "",
    category: str = "",
    min_price: float | None = None,
    max_price: float | None = None,
    city: str = "",
    seller: str = "",
    sort: str = "newest",
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
):
    return svc.list_listings(
        db,
        q=q,
        category=category,
        min_price=min_price,
        max_price=max_price,
        city=city,
        seller=seller,
        sort=sort,
        page=page,
        page_size=page_size,
    )


@router.get("/mine")
def my_listings(
    user=Depends(get_current_user),
    db=Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
):
    return svc.mine(db, user, page=page, page_size=page_size)


@router.get("/{listing_id}")
def get_listing(listing_id: str, db=Depends(get_db)):
    return svc.get(db, listing_id)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_listing(
    payload: ListingCreate,
    user=Depends(require_permission("listing.manage")),
    db=Depends(get_db),
):
    return svc.create(db, user, payload.model_dump())


@router.patch("/{listing_id}")
def update_listing(
    listing_id: str,
    payload: ListingUpdate,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    return svc.update(db, user, listing_id, payload.model_dump(exclude_unset=True, exclude_none=True))


@router.delete("/{listing_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_listing(listing_id: str, user=Depends(get_current_user), db=Depends(get_db)):
    svc.delete(db, user, listing_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{listing_id}/report", status_code=status.HTTP_202_ACCEPTED)
def report_listing(listing_id: str, body: dict | None = None, user=Depends(get_current_user), db=Depends(get_db)):
    svc.report(db, user, listing_id, (body or {}).get("reason", ""))
    return {"reported": True}