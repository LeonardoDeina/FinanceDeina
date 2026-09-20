import datetime as dt
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class CurrencyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    name: str
    symbol: str
    decimal_places: int
    is_active: bool


class CurrencyCreate(BaseModel):
    code: str = Field(min_length=3, max_length=3)
    name: str
    symbol: str
    decimal_places: int = 2


class ExchangeRateCreate(BaseModel):
    base_code: str = Field(min_length=3, max_length=3)
    quote_code: str = Field(min_length=3, max_length=3)
    rate_date: dt.date
    rate: Decimal
    source: str = "MANUAL"


class ExchangeRateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    base_code: str
    quote_code: str
    rate_date: dt.date
    rate: Decimal
    source: str


class ConversionQuoteResponse(BaseModel):
    from_code: str
    to_code: str
    on_date: dt.date
    rate: Decimal
    amount: Decimal
    converted_amount: Decimal
