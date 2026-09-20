import datetime as dt
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator

VALID_STATUSES = {"PLANNED", "PENDING", "CLEARED", "CANCELLED"}
VALID_TYPES = {"INCOME", "EXPENSE"}


class TransactionCreate(BaseModel):
    account_id: int
    category_id: int | None = None
    transaction_type: str
    status: str = "PLANNED"
    description: str
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    planned_amount: Decimal | None = None
    actual_amount: Decimal | None = None
    planned_date: dt.date | None = None
    actual_date: dt.date | None = None
    source_type: str = "MANUAL"
    notes: str | None = None
    tags: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def check_consistency(self) -> "TransactionCreate":
        if self.transaction_type.upper() not in VALID_TYPES:
            raise ValueError(f"transaction_type deve ser um de {VALID_TYPES}")
        if self.status.upper() not in VALID_STATUSES:
            raise ValueError(f"status deve ser um de {VALID_STATUSES}")
        if self.planned_amount is None and self.actual_amount is None:
            raise ValueError("Informe ao menos planned_amount ou actual_amount.")
        if self.status.upper() == "CLEARED" and (self.actual_amount is None or self.actual_date is None):
            raise ValueError("Status CLEARED exige actual_amount e actual_date.")
        return self


class TransactionUpdate(BaseModel):
    category_id: int | None = None
    description: str | None = None
    status: str | None = None
    planned_amount: Decimal | None = None
    actual_amount: Decimal | None = None
    planned_date: dt.date | None = None
    actual_date: dt.date | None = None
    notes: str | None = None
    tags: list[str] | None = None


class TransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    account_id: int
    category_id: int | None
    transaction_type: str
    status: str
    description: str
    currency: str
    planned_amount: Decimal | None
    actual_amount: Decimal | None
    planned_date: dt.date | None
    actual_date: dt.date | None
    source_type: str
    source_reference: str | None
    recurring_rule_id: int | None
    notes: str | None
    tags: list[str] = Field(default_factory=list)


class TransferCreate(BaseModel):
    source_account_id: int
    destination_account_id: int
    amount: Decimal = Field(gt=0)
    transfer_date: dt.date
    description: str | None = None

    @model_validator(mode="after")
    def check_accounts(self) -> "TransferCreate":
        if self.source_account_id == self.destination_account_id:
            raise ValueError("Conta de origem e destino devem ser diferentes.")
        return self


class TransferRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_account_id: int
    destination_account_id: int
    amount: Decimal
    source_currency: str
    destination_amount: Decimal
    destination_currency: str
    exchange_rate: Decimal
    transfer_date: dt.date
    description: str | None
