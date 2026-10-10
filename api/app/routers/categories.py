"""Category routes (read public, write moderator/admin)."""

from fastapi import APIRouter, Depends, Response, status

from ..core.mongo import get_db
from ..dependencies import require_permission
from ..schemas import CategoryCreate, CategoryUpdate
from ..services import categories as svc

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("")
def list_categories(db=Depends(get_db)):
    return {"items": svc.list_categories(db)}


@router.post("", status_code=status.HTTP_201_CREATED)
def create_category(payload: CategoryCreate, _=Depends(require_permission("category.manage")), db=Depends(get_db)):
    return svc.create(db, payload.model_dump())


@router.patch("/{slug}")
def update_category(slug: str, payload: CategoryUpdate, _=Depends(require_permission("category.manage")), db=Depends(get_db)):
    return svc.update(db, slug, payload.model_dump(exclude_unset=True, exclude_none=True))


@router.delete("/{slug}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(slug: str, _=Depends(require_permission("category.manage")), db=Depends(get_db)):
    svc.delete(db, slug)
    return Response(status_code=status.HTTP_204_NO_CONTENT)