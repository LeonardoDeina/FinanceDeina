import datetime as dt
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator

VALID_FREQUENCIES = {"WEEKLY", "BIWEEKLY", "MONTHLY", "QUARTERLY", "SEMIANNUAL", "ANNUAL"}


class RecurringRuleCreate(BaseModel):
    account_id: int
    category_id: int | None = None
    transaction_type: str
    description: str
    amount: Decimal = Field(gt=0)
    frequency: str
    start_date: dt.date
    end_date: dt.date | None = None

    @model_validator(mode="after")
    def check_frequency(self) -> "RecurringRuleCreate":
        if self.frequency.upper() not in VALID_FREQUENCIES:
            raise ValueError(f"frequency deve ser um de {VALID_FREQUENCIES}")
        return self


class RecurringRuleUpdate(BaseModel):
    description: str | None = None
    amount: Decimal | None = None
    end_date: dt.date | None = None
    is_active: bool | None = None


class RecurringRuleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    account_id: int
    category_id: int | None
    transaction_type: str
    description: str
    amount: Decimal
    frequency: str
    start_date: dt.date
    end_date: dt.date | None
    next_occurrence: dt.date
    is_active: bool


class UpcomingOccurrence(BaseModel):
    rule_id: int
    occurrence_date: dt.date
    description: str
    amount: Decimal
    transaction_type: str
