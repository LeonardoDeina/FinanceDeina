import datetime as dt
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.accounts.models import Account
from app.budgets.models import Budget, BudgetLine
from app.currency import service as currency_service
from app.recurring.models import RecurringRule
from app.recurring.service import occurrences_between
from app.reports.aggregation import account_balances, month_bounds
from app.reports.calculations import residual_budget
from app.transactions.models import Transaction

FUTURE_STATUSES = ("PLANNED", "PENDING")


@dataclass
class ForecastEvent:
    event_date: dt.date
    currency: str
    transaction_type: str  # INCOME | EXPENSE
    amount: Decimal
    category_id: int | None
    origin: str


def _manual_events(db: Session, user_id: int, start: dt.date, end: dt.date) -> list[ForecastEvent]:
    rows = db.execute(
        select(Transaction.planned_date, Transaction.currency, Transaction.transaction_type, Transaction.planned_amount, Transaction.category_id)
        .where(
            Transaction.user_id == user_id,
            Transaction.status.in_(FUTURE_STATUSES),
            Transaction.planned_date.is_not(None),
            Transaction.planned_amount.is_not(None),
            Transaction.planned_date >= start,
            Transaction.planned_date <= end,
        )
    ).all()
    return [
        ForecastEvent(planned_date, currency, ttype, Decimal(amount), category_id, "MANUAL")
        for planned_date, currency, ttype, amount, category_id in rows
    ]


def _materialized_recurring_dates(db: Session, rule_id: int, start: dt.date, end: dt.date) -> set[dt.date]:
    rows = db.execute(
        select(Transaction.planned_date).where(
            Transaction.recurring_rule_id == rule_id,
            Transaction.planned_date >= start,
            Transaction.planned_date <= end,
        )
    ).scalars()
    return set(rows)


def _recurring_events(db: Session, user_id: int, start: dt.date, end: dt.date) -> list[ForecastEvent]:
    rules = db.execute(
        select(RecurringRule).where(
            RecurringRule.user_id == user_id,
            RecurringRule.is_active.is_(True),
            RecurringRule.start_date <= end,
        )
    ).scalars()

    events: list[ForecastEvent] = []
    for rule in rules:
        account = db.get(Account, rule.account_id)
        already_materialized = _materialized_recurring_dates(db, rule.id, start, end)
        for occurrence_date in occurrences_between(rule.start_date, rule.frequency, start, end, rule.end_date):
            if occurrence_date in already_materialized:
                continue  # a manual transaction already represents this occurrence; avoid double counting
            events.append(
                ForecastEvent(occurrence_date, account.currency, rule.transaction_type, rule.amount, rule.category_id, "RECURRING")
            )
    return events


def _budget_residual_events(db: Session, user_id: int, base_currency: str, start: dt.date, end: dt.date, known_events: list[ForecastEvent]) -> list[ForecastEvent]:
    """Adds a category's remaining budget as a projected expense on the last
    day of its month, but only the portion not already covered by planned
    manual/recurring transactions in that category (spec 7.4)."""
    events: list[ForecastEvent] = []
    month_cursor = start.replace(day=1)
    while month_cursor <= end:
        month_start, month_end = month_bounds(month_cursor)
        budgets = db.execute(
            select(Budget).where(
                Budget.user_id == user_id,
                Budget.period_start <= month_end,
                Budget.period_end >= month_start,
                Budget.status == "ACTIVE",
            )
        ).scalars()
        for budget in budgets:
            for line in budget.lines:
                already_planned = sum(
                    (
                        e.amount
                        for e in known_events
                        if e.category_id == line.category_id
                        and e.transaction_type == "EXPENSE"
                        and month_start <= e.event_date <= month_end
                    ),
                    Decimal("0.00"),
                )
                residual = residual_budget(line.planned_amount, already_planned)
                if residual > 0:
                    events.append(ForecastEvent(month_end, base_currency, "EXPENSE", residual, line.category_id, "BUDGET_RESIDUAL"))
        month_cursor = (month_start.replace(day=28) + dt.timedelta(days=4)).replace(day=1)
    return events


@dataclass
class ForecastMonthSummary:
    reference_month: dt.date
    projected_income: Decimal
    projected_expenses: Decimal
    projected_savings: Decimal
    projected_end_balance: Decimal


@dataclass
class ForecastResult:
    starting_balance: Decimal
    horizon_end: dt.date
    currency: str
    monthly_summaries: list[ForecastMonthSummary]
    balance_on_horizon_end: Decimal


def run_forecast(
    db: Session, user, horizon_end: dt.date, account_ids: list[int] | None = None, as_of: dt.date | None = None
) -> ForecastResult:
    """Projects balance from today's real accounts plus known future events
    (7.3): manual future transactions, recurring occurrences and residual
    budget, converted day-by-day into the user's base currency so accounts
    in different currencies combine into one projection (RB-001 kept via
    Decimal throughout).
    """
    base_currency = user.base_currency
    today = as_of or dt.date.today()

    query = select(Account).where(Account.user_id == user.id, Account.is_active.is_(True))
    if account_ids:
        query = query.where(Account.id.in_(account_ids))
    accounts = list(db.execute(query).scalars())

    balances = account_balances(db, accounts, base_currency, today)
    # Accounts whose currency has no exchange rate yet contribute 0 instead of
    # aborting the whole forecast; the user still sees them in /accounts with
    # balance_in_base_currency=None as a prompt to add the missing rate.
    starting_balance = sum(
        (view.balance_in_base_currency for view in balances if view.balance_in_base_currency is not None),
        Decimal("0.00"),
    )

    manual = _manual_events(db, user.id, today, horizon_end)
    recurring = _recurring_events(db, user.id, today, horizon_end)
    residual = _budget_residual_events(db, user.id, base_currency, today, horizon_end, manual + recurring)
    events = sorted(manual + recurring + residual, key=lambda e: e.event_date)

    running_balance = starting_balance
    monthly_summaries: list[ForecastMonthSummary] = []
    month_cursor = today.replace(day=1)
    balance_on_horizon_end = starting_balance

    while month_cursor <= horizon_end:
        month_start, month_end = month_bounds(month_cursor)
        window_end = min(month_end, horizon_end)
        month_income = Decimal("0.00")
        month_expenses = Decimal("0.00")
        for event in events:
            if not (max(month_start, today) <= event.event_date <= window_end):
                continue
            converted = currency_service.convert(db, event.amount, event.currency, base_currency, event.event_date, base_currency)
            if event.transaction_type == "INCOME":
                month_income += converted
            else:
                month_expenses += converted
        month_savings = month_income - month_expenses
        running_balance += month_savings
        monthly_summaries.append(
            ForecastMonthSummary(
                reference_month=month_start,
                projected_income=month_income,
                projected_expenses=month_expenses,
                projected_savings=month_savings,
                projected_end_balance=running_balance,
            )
        )
        if window_end == horizon_end:
            balance_on_horizon_end = running_balance
        month_cursor = (month_start.replace(day=28) + dt.timedelta(days=4)).replace(day=1)

    return ForecastResult(
        starting_balance=starting_balance,
        horizon_end=horizon_end,
        currency=base_currency,
        monthly_summaries=monthly_summaries,
        balance_on_horizon_end=balance_on_horizon_end,
    )
