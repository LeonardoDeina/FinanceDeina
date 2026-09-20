import datetime as dt
from decimal import Decimal

from sqlalchemy.orm import Session

from app.accounts.models import Account
from app.budgets.models import Budget, BudgetLine
from app.categories.models import Category
from app.forecasting.service import run_forecast
from app.recurring.models import RecurringRule
from app.transactions.models import Transaction
from app.users.models import User


def test_forecast_starts_from_current_balance_and_projects_recurring_income(
    db: Session, user: User, eur_account: Account
):
    db.add(
        RecurringRule(
            user_id=user.id, account_id=eur_account.id, transaction_type="INCOME",
            description="Salário", amount=Decimal("2000.00"), frequency="MONTHLY",
            start_date=dt.date(2026, 1, 1), next_occurrence=dt.date(2026, 1, 1),
        )
    )
    db.commit()

    as_of = dt.date(2026, 1, 1)
    result = run_forecast(db, user, horizon_end=dt.date(2026, 3, 1), as_of=as_of)

    assert result.starting_balance == Decimal("1000.00")
    # Jan, Feb, Mar each get one 2000 salary occurrence
    assert len(result.monthly_summaries) == 3
    assert all(m.projected_income == Decimal("2000.00") for m in result.monthly_summaries)
    assert result.balance_on_horizon_end == Decimal("1000.00") + Decimal("2000.00") * 3


def test_forecast_does_not_double_count_materialized_recurring_occurrence(
    db: Session, user: User, eur_account: Account
):
    rule = RecurringRule(
        user_id=user.id, account_id=eur_account.id, transaction_type="INCOME",
        description="Salário", amount=Decimal("2000.00"), frequency="MONTHLY",
        start_date=dt.date(2026, 1, 1), next_occurrence=dt.date(2026, 1, 1),
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)

    # January occurrence was already turned into an explicit planned transaction
    db.add(
        Transaction(
            user_id=user.id, account_id=eur_account.id, category_id=None, transaction_type="INCOME",
            status="PLANNED", description="Salário Jan", currency="EUR", planned_amount=Decimal("2000.00"),
            planned_date=dt.date(2026, 1, 1), source_type="RECURRING_GENERATION", recurring_rule_id=rule.id,
        )
    )
    db.commit()

    result = run_forecast(db, user, horizon_end=dt.date(2026, 1, 31), as_of=dt.date(2026, 1, 1))

    # Only one 2000 counted for January, not 4000 (manual + recurring duplicate)
    assert result.monthly_summaries[0].projected_income == Decimal("2000.00")


def test_forecast_adds_only_uncovered_budget_residual(db: Session, user: User, eur_account: Account):
    category = Category(user_id=user.id, name="Mercado", category_type="EXPENSE")
    db.add(category)
    db.commit()
    db.refresh(category)

    budget = Budget(
        user_id=user.id, period_start=dt.date(2026, 1, 1), period_end=dt.date(2026, 1, 31),
        name="Janeiro", status="ACTIVE",
        lines=[BudgetLine(category_id=category.id, planned_amount=Decimal("400.00"))],
    )
    db.add(budget)
    # 250 of the 400 grocery budget is already covered by a specific planned transaction
    db.add(
        Transaction(
            user_id=user.id, account_id=eur_account.id, category_id=category.id, transaction_type="EXPENSE",
            status="PLANNED", description="Compra grande", currency="EUR", planned_amount=Decimal("250.00"),
            planned_date=dt.date(2026, 1, 15), source_type="MANUAL",
        )
    )
    db.commit()

    result = run_forecast(db, user, horizon_end=dt.date(2026, 1, 31), as_of=dt.date(2026, 1, 1))

    # 250 explicit + 150 residual = 400 total, never the full 400 + 250 double count
    assert result.monthly_summaries[0].projected_expenses == Decimal("400.00")
