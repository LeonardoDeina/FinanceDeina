import datetime as dt
from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.accounts.models import Account
from app.accounts.schemas import AccountRead, AccountWithBalance
from app.categories.models import Category
from app.currency import service as currency_service
from app.db.session import get_db
from app.reports.aggregation import (
    account_balances,
    actual_totals,
    convert_period_totals,
    month_bounds,
    planned_totals,
    planned_vs_actual_by_category,
)
from app.reports.calculations import absolute_variance, percentage_variance, realized_savings, savings_rate
from app.reports.schemas import CurrencyBreakdown, DashboardResponse, PlannedVsActualLine, PlannedVsActualResponse
from app.users.service import get_or_create_profile

router = APIRouter(tags=["reports"])


@router.get("/dashboard", response_model=DashboardResponse)
def dashboard(month: dt.date | None = None, db: Session = Depends(get_db)):
    profile = get_or_create_profile(db)
    reference_month = month or dt.date.today()
    start, end = month_bounds(reference_month)
    today = dt.date.today()
    balance_as_of = min(end, today)

    accounts = list(
        db.execute(select(Account).where(Account.user_id == profile.id, Account.is_active.is_(True))).scalars()
    )
    balance_views = account_balances(db, accounts, profile.base_currency, balance_as_of)

    accounts_with_balance = [
        AccountWithBalance(
            **AccountRead.model_validate(v.account).model_dump(),
            balance=v.balance,
            balance_in_base_currency=v.balance_in_base_currency,
            base_currency=profile.base_currency,
        )
        for v in balance_views
    ]
    balance_by_currency: dict[str, Decimal] = {}
    for v in balance_views:
        balance_by_currency[v.account.currency] = balance_by_currency.get(v.account.currency, Decimal("0.00")) + v.balance
    # Accounts in a currency with no exchange rate yet are skipped here (still
    # listed individually above with balance_in_base_currency=None) rather
    # than failing the whole dashboard.
    total_balance = sum(
        (v.balance_in_base_currency for v in balance_views if v.balance_in_base_currency is not None), Decimal("0.00")
    )

    planned = planned_totals(db, profile.id, start, end)
    actual = actual_totals(db, profile.id, start, end)
    planned_income, planned_expenses = convert_period_totals(db, planned, profile.base_currency, end)
    actual_income, actual_expenses = convert_period_totals(db, actual, profile.base_currency, end)
    planned_savings = realized_savings(planned_income, planned_expenses)
    actual_savings = realized_savings(actual_income, actual_expenses)

    return DashboardResponse(
        reference_month=start,
        base_currency=profile.base_currency,
        accounts=accounts_with_balance,
        total_balance_base_currency=total_balance,
        balance_by_account_currency=balance_by_currency,
        planned_income=planned_income,
        planned_expenses=planned_expenses,
        planned_savings=planned_savings,
        actual_income=actual_income,
        actual_expenses=actual_expenses,
        actual_savings=actual_savings,
        savings_rate=savings_rate(actual_savings, actual_income),
        actual_by_currency=[CurrencyBreakdown(currency=c, income=a.income, expenses=a.expenses) for c, a in actual.by_currency.items()],
        planned_by_currency=[CurrencyBreakdown(currency=c, income=a.income, expenses=a.expenses) for c, a in planned.by_currency.items()],
    )


@router.get("/reports/planned-vs-actual", response_model=PlannedVsActualResponse)
def planned_vs_actual(month: dt.date, db: Session = Depends(get_db)):
    profile = get_or_create_profile(db)
    start, end = month_bounds(month)
    by_category = planned_vs_actual_by_category(db, profile.id, start, end, profile.base_currency)

    categories = {c.id: c.name for c in db.execute(select(Category).where(Category.user_id == profile.id)).scalars()}

    lines = []
    for category_id, values in by_category.items():
        lines.append(
            PlannedVsActualLine(
                category_id=category_id,
                category_name=categories.get(category_id, "Sem categoria"),
                planned=values["planned"],
                actual=values["actual"],
                variance=absolute_variance(values["actual"], values["planned"]),
                variance_pct=percentage_variance(values["actual"], values["planned"]),
            )
        )
    lines.sort(key=lambda line: line.variance, reverse=True)
    return PlannedVsActualResponse(reference_month=start, base_currency=profile.base_currency, lines=lines)
