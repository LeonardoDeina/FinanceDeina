import datetime as dt
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class AccountCreate(BaseModel):
    name: str
    account_type: str = Field(description="CHECKING, SAVINGS, CASH, INVESTMENT, WALLET")
    currency: str = Field(min_length=3, max_length=3)
    initial_balance: Decimal = Decimal("0.00")
    initial_balance_date: dt.date


class AccountUpdate(BaseModel):
    name: str | None = None
    account_type: str | None = None
    is_active: bool | None = None


class AccountBalanceAdjustment(BaseModel):
    new_balance: Decimal
    as_of: dt.date
    reason: str


class AccountRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    account_type: str
    currency: str
    initial_balance: Decimal
    initial_balance_date: dt.date
    is_active: bool


class AccountWithBalance(AccountRead):
    balance: Decimal
    balance_in_base_currency: Decimal | None
    base_currency: str
