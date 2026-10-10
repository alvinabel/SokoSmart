"""Profile routes."""

from fastapi import APIRouter, Depends, status

from ..core.db import get_db
from ..dependencies import get_current_user
from ..schemas import BecomeSeller, ProfileUpdate
from ..services import profile as svc

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("/me")
def my_profile(user=Depends(get_current_user), db=Depends(get_db)):
    return svc.me(db, user)


@router.patch("/me")
def update_profile(payload: ProfileUpdate, user=Depends(get_current_user), db=Depends(get_db)):
    return svc.update(db, user, payload.model_dump(exclude_unset=True))


@router.post("/become-seller", status_code=status.HTTP_200_OK)
def become_seller(payload: BecomeSeller | None = None, user=Depends(get_current_user), db=Depends(get_db)):
    return svc.become_seller(db, user)


@router.get("/{user_id}")
def public_profile(user_id: str, db=Depends(get_db)):
    return svc.public_profile(db, user_id)