import calendar
import datetime as dt
from dataclasses import dataclass, field
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.accounts.models import Account
from app.currency import service as currency_service
from app.transactions.models import Transaction
from app.transactions.service import REALIZED_STATUS, account_balance


def month_bounds(reference_month: dt.date) -> tuple[dt.date, dt.date]:
    start = reference_month.replace(day=1)
    last_day = calendar.monthrange(start.year, start.month)[1]
    return start, start.replace(day=last_day)


@dataclass
class CurrencyAmounts:
    income: Decimal = Decimal("0.00")
    expenses: Decimal = Decimal("0.00")


@dataclass
class PeriodTotals:
    by_currency: dict[str, CurrencyAmounts] = field(default_factory=dict)

    def add(self, currency: str, transaction_type: str, amount: Decimal) -> None:
        bucket = self.by_currency.setdefault(currency, CurrencyAmounts())
        if transaction_type == "INCOME":
            bucket.income += amount
        else:
            bucket.expenses += amount


def _period_totals(db: Session, user_id: int, start: dt.date, end: dt.date, *, use_actual: bool) -> PeriodTotals:
    date_column = Transaction.actual_date if use_actual else Transaction.planned_date
    amount_column = Transaction.actual_amount if use_actual else Transaction.planned_amount
    status_filter = (Transaction.status == REALIZED_STATUS) if use_actual else (Transaction.status != "CANCELLED")

    rows = db.execute(
        select(Transaction.currency, Transaction.transaction_type, func.coalesce(func.sum(amount_column), 0))
        .where(
            Transaction.user_id == user_id,
            date_column.is_not(None),
            date_column >= start,
            date_column <= end,
            status_filter,
        )
        .group_by(Transaction.currency, Transaction.transaction_type)
    ).all()

    totals = PeriodTotals()
    for currency, transaction_type, amount in rows:
        totals.add(currency, transaction_type, Decimal(amount))
    return totals


def planned_totals(db: Session, user_id: int, start: dt.date, end: dt.date) -> PeriodTotals:
    return _period_totals(db, user_id, start, end, use_actual=False)


def actual_totals(db: Session, user_id: int, start: dt.date, end: dt.date) -> PeriodTotals:
    return _period_totals(db, user_id, start, end, use_actual=True)


def convert_period_totals(
    db: Session, totals: PeriodTotals, base_currency: str, on_date: dt.date
) -> tuple[Decimal, Decimal]:
    """Sum every currency bucket into the user's base currency for the headline dashboard numbers.

    Per-currency figures (`totals.by_currency`) stay available for callers
    that want to show the breakdown instead of a single converted total.
    """
    total_income = Decimal("0.00")
    total_expenses = Decimal("0.00")
    for currency, amounts in totals.by_currency.items():
        total_income += currency_service.convert(db, amounts.income, currency, base_currency, on_date, base_currency)
        total_expenses += currency_service.convert(
            db, amounts.expenses, currency, base_currency, on_date, base_currency
        )
    return total_income, total_expenses


def planned_vs_actual_by_category(
    db: Session, user_id: int, start: dt.date, end: dt.date, base_currency: str
) -> dict[int | None, dict[str, Decimal]]:
    """Category-level planned x actual expense totals, each already
    converted into the base currency (spec 10.2 / DSH-002)."""
    planned_rows = db.execute(
        select(Transaction.category_id, Transaction.currency, func.coalesce(func.sum(Transaction.planned_amount), 0))
        .where(
            Transaction.user_id == user_id,
            Transaction.status != "CANCELLED",
            Transaction.planned_date.is_not(None),
            Transaction.planned_date >= start,
            Transaction.planned_date <= end,
        )
        .group_by(Transaction.category_id, Transaction.currency)
    ).all()
    actual_rows = db.execute(
        select(Transaction.category_id, Transaction.currency, func.coalesce(func.sum(Transaction.actual_amount), 0))
        .where(
            Transaction.user_id == user_id,
            Transaction.status == REALIZED_STATUS,
            Transaction.actual_date.is_not(None),
            Transaction.actual_date >= start,
            Transaction.actual_date <= end,
        )
        .group_by(Transaction.category_id, Transaction.currency)
    ).all()

    result: dict[int | None, dict[str, Decimal]] = {}

    def add(rows, key: str) -> None:
        for category_id, currency, amount in rows:
            converted = currency_service.convert(db, Decimal(amount), currency, base_currency, end, base_currency)
            bucket = result.setdefault(category_id, {"planned": Decimal("0.00"), "actual": Decimal("0.00")})
            bucket[key] += converted

    add(planned_rows, "planned")
    add(actual_rows, "actual")
    return result


@dataclass
class AccountBalanceView:
    account: Account
    balance: Decimal
    balance_in_base_currency: Decimal | None


def account_balances(
    db: Session, accounts: list[Account], base_currency: str, as_of: dt.date
) -> list[AccountBalanceView]:
    """Converts each account's balance into the base currency for display.

    An account in a currency with no exchange rate registered yet still
    shows its own balance; `balance_in_base_currency` is None instead of
    raising, so the dashboard/account list keeps working while the user
    fills in that rate.
    """
    views = []
    for account in accounts:
        balance = account_balance(db, account, as_of)
        try:
            converted = currency_service.convert(db, balance, account.currency, base_currency, as_of, base_currency)
        except currency_service.MissingExchangeRateError:
            converted = None
        views.append(AccountBalanceView(account=account, balance=balance, balance_in_base_currency=converted))
    return views
