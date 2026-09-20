import datetime as dt

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.closings.schemas import MonthlyClosingRead, ReopenRequest
from app.closings.service import ClosingAlreadyClosedError, ClosingNotFoundError, close_month, get_or_build_snapshot, reopen_month
from app.db.session import get_db
from app.users.service import get_or_create_profile

router = APIRouter(prefix="/closings", tags=["closings"])


@router.get("/{reference_month}/preview", response_model=MonthlyClosingRead)
def preview_closing(reference_month: dt.date, db: Session = Depends(get_db)):
    profile = get_or_create_profile(db)
    return get_or_build_snapshot(db, profile, reference_month)


@router.post("/{reference_month}/close", response_model=MonthlyClosingRead)
def close(reference_month: dt.date, db: Session = Depends(get_db)):
    profile = get_or_create_profile(db)
    try:
        return close_month(db, profile, reference_month)
    except ClosingAlreadyClosedError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/{reference_month}/reopen", response_model=MonthlyClosingRead)
def reopen(reference_month: dt.date, payload: ReopenRequest, db: Session = Depends(get_db)):
    profile = get_or_create_profile(db)
    try:
        return reopen_month(db, profile, reference_month, payload.reason)
    except ClosingNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
