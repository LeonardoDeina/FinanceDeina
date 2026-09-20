import datetime as dt
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class MonthlyClosingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    reference_month: dt.date
    currency: str
    status: str
    planned_income: Decimal
    actual_income: Decimal
    planned_expenses: Decimal
    actual_expenses: Decimal
    planned_savings: Decimal
    actual_savings: Decimal
    reconciliation_coverage_pct: Decimal
    closed_at: dt.datetime | None
    reopen_reason: str | None
    snapshot_json: dict


class ReopenRequest(BaseModel):
    reason: str
