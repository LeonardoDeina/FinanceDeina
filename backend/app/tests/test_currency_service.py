import datetime as dt
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.currency import service
from app.currency.exceptions import MissingExchangeRateError
from app.tests.conftest import add_rate


def test_identity_conversion_needs_no_rate(db: Session, currencies):
    assert service.convert(db, Decimal("100.00"), "EUR", "EUR", dt.date(2026, 1, 1), "EUR") == Decimal("100.00")


def test_direct_rate_conversion(db: Session, currencies):
    add_rate(db, "EUR", "USD", Decimal("1.10"), dt.date(2026, 1, 1))
    result = service.convert(db, Decimal("100.00"), "EUR", "USD", dt.date(2026, 1, 15), "EUR")
    assert result == Decimal("110.00")


def test_inverse_rate_used_when_only_reverse_pair_known(db: Session, currencies):
    add_rate(db, "USD", "EUR", Decimal("0.90909091"), dt.date(2026, 1, 1))
    result = service.convert(db, Decimal("100.00"), "EUR", "USD", dt.date(2026, 1, 15), "EUR")
    assert result == Decimal("110.00")


def test_bridge_through_base_currency_when_pair_unknown(db: Session, currencies):
    # Only USD->EUR and BRL->EUR are known; USD->BRL must bridge through EUR.
    add_rate(db, "USD", "EUR", Decimal("0.90"), dt.date(2026, 1, 1))
    add_rate(db, "BRL", "EUR", Decimal("0.18"), dt.date(2026, 1, 1))
    result = service.get_rate(db, "USD", "BRL", dt.date(2026, 1, 15), "EUR")
    # 1 USD = 0.90 EUR; 1 BRL = 0.18 EUR => 1 EUR = 1/0.18 BRL => 1 USD = 0.90 / 0.18 BRL
    assert result == Decimal("0.90") / Decimal("0.18")


def test_uses_most_recent_rate_on_or_before_date(db: Session, currencies):
    add_rate(db, "EUR", "USD", Decimal("1.05"), dt.date(2026, 1, 1))
    add_rate(db, "EUR", "USD", Decimal("1.10"), dt.date(2026, 2, 1))
    assert service.get_rate(db, "EUR", "USD", dt.date(2026, 1, 20), "EUR") == Decimal("1.05")
    assert service.get_rate(db, "EUR", "USD", dt.date(2026, 2, 15), "EUR") == Decimal("1.10")


def test_missing_rate_raises(db: Session, currencies):
    with pytest.raises(MissingExchangeRateError):
        service.get_rate(db, "EUR", "USD", dt.date(2026, 1, 1), "EUR")
