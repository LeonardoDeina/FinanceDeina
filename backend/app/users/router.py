from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.users.schemas import ProfileRead, ProfileUpdate
from app.users.service import get_or_create_profile

router = APIRouter(tags=["profile"])


@router.get("/profile", response_model=ProfileRead)
def read_profile(db: Session = Depends(get_db)) -> ProfileRead:
    return get_or_create_profile(db)


@router.put("/profile", response_model=ProfileRead)
def update_profile(payload: ProfileUpdate, db: Session = Depends(get_db)) -> ProfileRead:
    profile = get_or_create_profile(db)
    data = payload.model_dump(exclude_unset=True)
    if "base_currency" in data and data["base_currency"]:
        data["base_currency"] = data["base_currency"].upper()
    for field, value in data.items():
        setattr(profile, field, value)
    db.commit()
    db.refresh(profile)
    return profile
