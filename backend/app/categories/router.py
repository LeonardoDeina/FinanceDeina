from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.categories.models import Category
from app.categories.schemas import CategoryCreate, CategoryRead, CategoryUpdate
from app.db.session import get_db
from app.users.service import get_or_create_profile

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryRead])
def list_categories(include_archived: bool = False, db: Session = Depends(get_db)):
    profile = get_or_create_profile(db)
    query = select(Category).where(Category.user_id == profile.id)
    if not include_archived:
        query = query.where(Category.is_active.is_(True))
    return list(db.execute(query.order_by(Category.name)).scalars())


@router.post("", response_model=CategoryRead, status_code=201)
def create_category(payload: CategoryCreate, db: Session = Depends(get_db)):
    profile = get_or_create_profile(db)
    category = Category(
        user_id=profile.id,
        name=payload.name,
        category_type=payload.category_type.upper(),
        parent_id=payload.parent_id,
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.patch("/{category_id}", response_model=CategoryRead)
def update_category(category_id: int, payload: CategoryUpdate, db: Session = Depends(get_db)):
    profile = get_or_create_profile(db)
    category = db.get(Category, category_id)
    if category is None or category.user_id != profile.id:
        raise HTTPException(status_code=404, detail="Categoria não encontrada.")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(category, field, value)
    db.commit()
    db.refresh(category)
    return category
