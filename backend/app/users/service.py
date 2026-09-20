from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.users.models import User


def get_or_create_profile(db: Session) -> User:
    """V1 is single-user; this returns the one local profile, creating it
    with sane defaults on first access so every other module can rely on it
    existing (base currency, timezone)."""
    user = db.execute(select(User).order_by(User.id).limit(1)).scalar_one_or_none()
    if user is not None:
        return user

    settings = get_settings()
    user = User(name="Minha conta", base_currency=settings.default_base_currency, timezone=settings.default_timezone)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
