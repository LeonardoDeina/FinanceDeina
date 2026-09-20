import datetime as dt

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.accounts.models import Account
from app.db.session import get_db
from app.recurring.models import RecurringRule
from app.recurring.schemas import RecurringRuleCreate, RecurringRuleRead, RecurringRuleUpdate, UpcomingOccurrence
from app.recurring.service import next_occurrence_after, occurrences_between
from app.users.service import get_or_create_profile

router = APIRouter(prefix="/recurring-rules", tags=["recurring"])


@router.get("", response_model=list[RecurringRuleRead])
def list_rules(include_inactive: bool = False, db: Session = Depends(get_db)):
    profile = get_or_create_profile(db)
    query = select(RecurringRule).where(RecurringRule.user_id == profile.id)
    if not include_inactive:
        query = query.where(RecurringRule.is_active.is_(True))
    return list(db.execute(query.order_by(RecurringRule.next_occurrence)).scalars())


@router.post("", response_model=RecurringRuleRead, status_code=201)
def create_rule(payload: RecurringRuleCreate, db: Session = Depends(get_db)):
    profile = get_or_create_profile(db)
    account = db.get(Account, payload.account_id)
    if account is None or account.user_id != profile.id:
        raise HTTPException(status_code=404, detail="Conta não encontrada.")

    frequency = payload.frequency.upper()
    next_occurrence = payload.start_date if payload.start_date >= dt.date.today() else next_occurrence_after(
        payload.start_date, frequency
    )

    rule = RecurringRule(
        user_id=profile.id,
        account_id=account.id,
        category_id=payload.category_id,
        transaction_type=payload.transaction_type.upper(),
        description=payload.description,
        amount=payload.amount,
        frequency=frequency,
        start_date=payload.start_date,
        end_date=payload.end_date,
        next_occurrence=next_occurrence,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.patch("/{rule_id}", response_model=RecurringRuleRead)
def update_rule(rule_id: int, payload: RecurringRuleUpdate, db: Session = Depends(get_db)):
    profile = get_or_create_profile(db)
    rule = db.get(RecurringRule, rule_id)
    if rule is None or rule.user_id != profile.id:
        raise HTTPException(status_code=404, detail="Recorrência não encontrada.")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(rule, field, value)
    db.commit()
    db.refresh(rule)
    return rule


@router.get("/upcoming", response_model=list[UpcomingOccurrence])
def upcoming_occurrences(horizon_days: int = 30, db: Session = Depends(get_db)):
    profile = get_or_create_profile(db)
    today = dt.date.today()
    horizon = today + dt.timedelta(days=horizon_days)
    rules = db.execute(
        select(RecurringRule).where(RecurringRule.user_id == profile.id, RecurringRule.is_active.is_(True))
    ).scalars()

    results: list[UpcomingOccurrence] = []
    for rule in rules:
        for occurrence_date in occurrences_between(rule.start_date, rule.frequency, today, horizon, rule.end_date):
            results.append(
                UpcomingOccurrence(
                    rule_id=rule.id,
                    occurrence_date=occurrence_date,
                    description=rule.description,
                    amount=rule.amount,
                    transaction_type=rule.transaction_type,
                )
            )
    return sorted(results, key=lambda o: o.occurrence_date)
