import datetime as dt
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.budgets.models import Budget, BudgetLine
from app.currency import service as currency_service
from app.reports.calculations import absolute_variance, percentage_variance
from app.transactions.models import Transaction


@dataclass
class BudgetLineProgress:
    line: BudgetLine
    actual_spent: Decimal
    remaining: Decimal
    used_pct: Decimal
    variance: Decimal
    variance_pct: Decimal | None


def line_progress(db: Session, budget: Budget, line: BudgetLine, base_currency: str) -> BudgetLineProgress:
    rows = db.execute(
        select(Transaction.currency, func.coalesce(func.sum(Transaction.actual_amount), 0))
        .where(
            Transaction.category_id == line.category_id,
            Transaction.transaction_type == "EXPENSE",
            Transaction.status == "CLEARED",
            Transaction.actual_date.is_not(None),
            Transaction.actual_date >= budget.period_start,
            Transaction.actual_date <= budget.period_end,
        )
        .group_by(Transaction.currency)
    ).all()

    actual_spent = Decimal("0.00")
    for currency, amount in rows:
        actual_spent += currency_service.convert(
            db, Decimal(amount), currency, base_currency, budget.period_end, base_currency
        )

    remaining = line.planned_amount - actual_spent
    used_pct = (actual_spent / line.planned_amount * Decimal("100")).quantize(Decimal("0.01")) if line.planned_amount else Decimal("0.00")

    return BudgetLineProgress(
        line=line,
        actual_spent=actual_spent,
        remaining=remaining,
        used_pct=used_pct,
        variance=absolute_variance(actual_spent, line.planned_amount),
        variance_pct=percentage_variance(actual_spent, line.planned_amount),
    )


def copy_budget(db: Session, source: Budget, new_period_start: dt.date, new_period_end: dt.date, new_name: str) -> Budget:
    """BUD-002: duplicate a budget's lines into a new editable period."""
    clone = Budget(
        user_id=source.user_id,
        period_start=new_period_start,
        period_end=new_period_end,
        name=new_name,
        status="DRAFT",
    )
    clone.lines = [
        BudgetLine(category_id=line.category_id, planned_amount=line.planned_amount, notes=line.notes)
        for line in source.lines
    ]
    db.add(clone)
    db.commit()
    db.refresh(clone)
    return clone
