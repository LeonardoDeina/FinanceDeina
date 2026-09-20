import datetime as dt
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ForecastRunRequest(BaseModel):
    horizon_days: int | None = Field(default=None, gt=0, le=1825)
    horizon_end: dt.date | None = None
    account_ids: list[int] | None = None
    scenario_name: str | None = None

    @model_validator(mode="after")
    def check_horizon(self) -> "ForecastRunRequest":
        if not self.horizon_days and not self.horizon_end:
            raise ValueError("Informe horizon_days ou horizon_end.")
        return self


class ForecastMonthlyItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    reference_month: dt.date
    projected_income: Decimal
    projected_expenses: Decimal
    projected_savings: Decimal
    projected_end_balance: Decimal


class ForecastRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    run_at: dt.datetime
    horizon_end: dt.date
    scenario_name: str | None
    currency: str
    starting_balance: Decimal
    projected_ending_balance: Decimal
    monthly_items: list[ForecastMonthlyItemRead]


class SavingsCapacityRead(BaseModel):
    average_3m: Decimal | None
    average_6m: Decimal | None
    average_12m: Decimal | None
    median_6m: Decimal | None
    trend: str
    recommended: Decimal
    currency: str
