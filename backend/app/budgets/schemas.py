import datetime as dt
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class BudgetLineCreate(BaseModel):
    category_id: int
    planned_amount: Decimal
    notes: str | None = None


class BudgetCreate(BaseModel):
    name: str
    period_start: dt.date
    period_end: dt.date
    lines: list[BudgetLineCreate] = []


class BudgetCopyRequest(BaseModel):
    new_period_start: dt.date
    new_period_end: dt.date
    new_name: str


class BudgetLineRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category_id: int
    planned_amount: Decimal
    notes: str | None


class BudgetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    period_start: dt.date
    period_end: dt.date
    status: str
    lines: list[BudgetLineRead]


class BudgetLineProgressRead(BaseModel):
    category_id: int
    planned_amount: Decimal
    actual_spent: Decimal
    remaining: Decimal
    used_pct: Decimal
    variance: Decimal
    variance_pct: Decimal | None


class BudgetProgressRead(BaseModel):
    budget: BudgetRead
    lines: list[BudgetLineProgressRead]
