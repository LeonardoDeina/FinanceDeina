import datetime as dt
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.money import quantize_money
from app.currency.exceptions import MissingExchangeRateError
from app.currency.models import ExchangeRate


def _latest_rate(db: Session, base_code: str, quote_code: str, on_date: dt.date) -> Decimal | None:
    stmt = (
        select(ExchangeRate.rate)
        .where(
            ExchangeRate.base_code == base_code,
            ExchangeRate.quote_code == quote_code,
            ExchangeRate.rate_date <= on_date,
        )
        .order_by(ExchangeRate.rate_date.desc())
        .limit(1)
    )
    return db.execute(stmt).scalar_one_or_none()


def get_rate(db: Session, from_code: str, to_code: str, on_date: dt.date, bridge_code: str) -> Decimal:
    """Return how many `to_code` units equal 1 `from_code` unit on/before `on_date`.

    Tries, in order: identity, direct rate, inverse of direct rate, and a
    two-leg bridge through `bridge_code` (the user's base currency), which
    covers pairs the user never entered directly (e.g. USD->BRL when only
    USD->EUR and BRL->EUR are known).
    """
    if from_code == to_code:
        return Decimal("1")

    direct = _latest_rate(db, from_code, to_code, on_date)
    if direct is not None:
        return direct

    inverse = _latest_rate(db, to_code, from_code, on_date)
    if inverse is not None and inverse != 0:
        return Decimal("1") / inverse

    if bridge_code not in (from_code, to_code):
        try:
            leg1 = get_rate(db, from_code, bridge_code, on_date, bridge_code)
            leg2 = get_rate(db, bridge_code, to_code, on_date, bridge_code)
            return leg1 * leg2
        except MissingExchangeRateError:
            pass

    raise MissingExchangeRateError(from_code, to_code)


def convert(
    db: Session, amount: Decimal, from_code: str, to_code: str, on_date: dt.date, bridge_code: str
) -> Decimal:
    if from_code == to_code:
        return quantize_money(amount)
    rate = get_rate(db, from_code, to_code, on_date, bridge_code)
    return quantize_money(amount * rate)
