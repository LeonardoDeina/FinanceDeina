import datetime as dt
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.closings.models import MonthlyClosing
from app.db.mixins import utcnow
from app.reports.aggregation import actual_totals, convert_period_totals, month_bounds, planned_totals
from app.reports.calculations import absolute_variance, realized_savings


class ClosingAlreadyClosedError(Exception):
    pass


class ClosingNotFoundError(Exception):
    pass


def get_or_build_snapshot(db: Session, user, reference_month: dt.date) -> MonthlyClosing:
    """Computes (without persisting) the current planned x realized picture
    for a month, so the UI can preview it before the user confirms closing."""
    month_start, month_end = month_bounds(reference_month)
    planned = planned_totals(db, user.id, month_start, month_end)
    actual = actual_totals(db, user.id, month_start, month_end)

    planned_income, planned_expenses = convert_period_totals(db, planned, user.base_currency, month_end)
    actual_income, actual_expenses = convert_period_totals(db, actual, user.base_currency, month_end)

    planned_savings = realized_savings(planned_income, planned_expenses)
    actual_savings = realized_savings(actual_income, actual_expenses)

    existing = db.execute(
        select(MonthlyClosing).where(MonthlyClosing.user_id == user.id, MonthlyClosing.reference_month == month_start)
    ).scalar_one_or_none()

    snapshot_json = {
        "planned_by_currency": {c: {"income": str(a.income), "expenses": str(a.expenses)} for c, a in planned.by_currency.items()},
        "actual_by_currency": {c: {"income": str(a.income), "expenses": str(a.expenses)} for c, a in actual.by_currency.items()},
        "income_variance": str(absolute_variance(actual_income, planned_income)),
        "expenses_variance": str(absolute_variance(actual_expenses, planned_expenses)),
        "savings_variance": str(absolute_variance(actual_savings, planned_savings)),
    }

    if existing is not None:
        closing = existing
    else:
        closing = MonthlyClosing(
            user_id=user.id,
            reference_month=month_start,
            currency=user.base_currency,
            status="OPEN",
            snapshot_json={},
        )
        db.add(closing)

    closing.planned_income = planned_income
    closing.actual_income = actual_income
    closing.planned_expenses = planned_expenses
    closing.actual_expenses = actual_expenses
    closing.planned_savings = planned_savings
    closing.actual_savings = actual_savings
    closing.snapshot_json = snapshot_json
    db.commit()
    db.refresh(closing)
    return closing


def close_month(db: Session, user, reference_month: dt.date, forecast_run_id: int | None = None) -> MonthlyClosing:
    closing = get_or_build_snapshot(db, user, reference_month)
    if closing.status == "CLOSED":
        raise ClosingAlreadyClosedError(f"O mês {reference_month:%Y-%m} já está fechado.")
    closing.status = "CLOSED"
    closing.closed_at = utcnow()
    closing.forecast_run_id = forecast_run_id
    db.commit()
    db.refresh(closing)
    return closing


def reopen_month(db: Session, user, reference_month: dt.date, reason: str) -> MonthlyClosing:
    month_start, _ = month_bounds(reference_month)
    closing = db.execute(
        select(MonthlyClosing).where(MonthlyClosing.user_id == user.id, MonthlyClosing.reference_month == month_start)
    ).scalar_one_or_none()
    if closing is None:
        raise ClosingNotFoundError(f"Nenhum fechamento encontrado para {reference_month:%Y-%m}.")
    closing.status = "REOPENED"
    closing.reopen_reason = reason
    db.commit()
    db.refresh(closing)
    return closing
