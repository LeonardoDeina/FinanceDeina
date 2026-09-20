from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.budgets.models import Budget, BudgetLine
from app.budgets.schemas import (
    BudgetCopyRequest,
    BudgetCreate,
    BudgetLineProgressRead,
    BudgetProgressRead,
    BudgetRead,
)
from app.budgets.service import copy_budget, line_progress
from app.db.session import get_db
from app.users.service import get_or_create_profile

router = APIRouter(prefix="/budgets", tags=["budgets"])


@router.get("", response_model=list[BudgetRead])
def list_budgets(db: Session = Depends(get_db)):
    profile = get_or_create_profile(db)
    query = (
        select(Budget)
        .where(Budget.user_id == profile.id)
        .options(selectinload(Budget.lines))
        .order_by(Budget.period_start.desc())
    )
    return list(db.execute(query).scalars())


@router.post("", response_model=BudgetRead, status_code=201)
def create_budget(payload: BudgetCreate, db: Session = Depends(get_db)):
    profile = get_or_create_profile(db)
    budget = Budget(
        user_id=profile.id,
        name=payload.name,
        period_start=payload.period_start,
        period_end=payload.period_end,
        status="ACTIVE",
        lines=[
            BudgetLine(category_id=line.category_id, planned_amount=line.planned_amount, notes=line.notes)
            for line in payload.lines
        ],
    )
    db.add(budget)
    db.commit()
    db.refresh(budget)
    return budget


@router.post("/{budget_id}/copy", response_model=BudgetRead, status_code=201)
def duplicate_budget(budget_id: int, payload: BudgetCopyRequest, db: Session = Depends(get_db)):
    profile = get_or_create_profile(db)
    source = db.get(Budget, budget_id)
    if source is None or source.user_id != profile.id:
        raise HTTPException(status_code=404, detail="Orçamento não encontrado.")
    return copy_budget(db, source, payload.new_period_start, payload.new_period_end, payload.new_name)


@router.get("/{budget_id}/progress", response_model=BudgetProgressRead)
def budget_progress(budget_id: int, db: Session = Depends(get_db)):
    profile = get_or_create_profile(db)
    budget = db.get(Budget, budget_id)
    if budget is None or budget.user_id != profile.id:
        raise HTTPException(status_code=404, detail="Orçamento não encontrado.")

    lines_progress = []
    for line in budget.lines:
        progress = line_progress(db, budget, line, profile.base_currency)
        lines_progress.append(
            BudgetLineProgressRead(
                category_id=line.category_id,
                planned_amount=line.planned_amount,
                actual_spent=progress.actual_spent,
                remaining=progress.remaining,
                used_pct=progress.used_pct,
                variance=progress.variance,
                variance_pct=progress.variance_pct,
            )
        )
    return BudgetProgressRead(budget=budget, lines=lines_progress)
