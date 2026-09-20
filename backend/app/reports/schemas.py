import datetime as dt
from decimal import Decimal

from pydantic import BaseModel

from app.accounts.schemas import AccountWithBalance


class CurrencyBreakdown(BaseModel):
    currency: str
    income: Decimal
    expenses: Decimal


class DashboardResponse(BaseModel):
    reference_month: dt.date
    base_currency: str
    accounts: list[AccountWithBalance]
    total_balance_base_currency: Decimal
    balance_by_account_currency: dict[str, Decimal]
    planned_income: Decimal
    planned_expenses: Decimal
    planned_savings: Decimal
    actual_income: Decimal
    actual_expenses: Decimal
    actual_savings: Decimal
    savings_rate: Decimal | None
    actual_by_currency: list[CurrencyBreakdown]
    planned_by_currency: list[CurrencyBreakdown]


class PlannedVsActualLine(BaseModel):
    category_id: int | None
    category_name: str
    planned: Decimal
    actual: Decimal
    variance: Decimal
    variance_pct: Decimal | None


class PlannedVsActualResponse(BaseModel):
    reference_month: dt.date
    base_currency: str
    lines: list[PlannedVsActualLine]
