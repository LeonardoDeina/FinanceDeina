import datetime as dt
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.currency import service
from app.currency.exceptions import MissingExchangeRateError
from app.currency.models import Currency, ExchangeRate
from app.currency.schemas import (
    ConversionQuoteResponse,
    CurrencyCreate,
    CurrencyRead,
    ExchangeRateCreate,
    ExchangeRateRead,
)
from app.db.session import get_db
from app.users.service import get_or_create_profile

router = APIRouter(tags=["currencies"])


@router.get("/currencies", response_model=list[CurrencyRead])
def list_currencies(db: Session = Depends(get_db)) -> list[Currency]:
    return list(db.execute(select(Currency).order_by(Currency.code)).scalars())


@router.post("/currencies", response_model=CurrencyRead, status_code=201)
def create_currency(payload: CurrencyCreate, db: Session = Depends(get_db)) -> Currency:
    currency = Currency(
        code=payload.code.upper(),
        name=payload.name,
        symbol=payload.symbol,
        decimal_places=payload.decimal_places,
    )
    db.add(currency)
    db.commit()
    db.refresh(currency)
    return currency


@router.get("/exchange-rates", response_model=list[ExchangeRateRead])
def list_exchange_rates(db: Session = Depends(get_db)) -> list[ExchangeRate]:
    stmt = select(ExchangeRate).order_by(ExchangeRate.rate_date.desc())
    return list(db.execute(stmt).scalars())


@router.post("/exchange-rates", response_model=ExchangeRateRead, status_code=201)
def create_exchange_rate(payload: ExchangeRateCreate, db: Session = Depends(get_db)) -> ExchangeRate:
    rate = ExchangeRate(
        base_code=payload.base_code.upper(),
        quote_code=payload.quote_code.upper(),
        rate_date=payload.rate_date,
        rate=payload.rate,
        source=payload.source,
    )
    db.add(rate)
    db.commit()
    db.refresh(rate)
    return rate


@router.get("/exchange-rates/convert", response_model=ConversionQuoteResponse)
def quote_conversion(
    from_code: str,
    to_code: str,
    amount: Decimal,
    on_date: dt.date | None = None,
    db: Session = Depends(get_db),
) -> ConversionQuoteResponse:
    profile = get_or_create_profile(db)
    target_date = on_date or dt.date.today()
    try:
        rate = service.get_rate(db, from_code.upper(), to_code.upper(), target_date, profile.base_currency)
    except MissingExchangeRateError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    converted = service.convert(db, amount, from_code.upper(), to_code.upper(), target_date, profile.base_currency)
    return ConversionQuoteResponse(
        from_code=from_code.upper(),
        to_code=to_code.upper(),
        on_date=target_date,
        rate=rate,
        amount=amount,
        converted_amount=converted,
    )
