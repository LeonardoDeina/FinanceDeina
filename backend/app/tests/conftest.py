import datetime as dt

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.accounts.models import Account
from app.currency.models import Currency, ExchangeRate
from app.db import models_registry  # noqa: F401 - registers all ORM tables
from app.db.base import Base
from app.users.models import User


@pytest.fixture()
def db() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, future=True)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture()
def currencies(db: Session) -> None:
    for code, name, symbol in [("EUR", "Euro", "€"), ("USD", "US Dollar", "$"), ("BRL", "Real", "R$")]:
        db.add(Currency(code=code, name=name, symbol=symbol, decimal_places=2))
    db.commit()


@pytest.fixture()
def user(db: Session, currencies: None) -> User:
    profile = User(name="Teste", base_currency="EUR", timezone="Europe/Lisbon")
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@pytest.fixture()
def eur_account(db: Session, user: User) -> Account:
    account = Account(
        user_id=user.id,
        name="Conta Corrente EUR",
        account_type="CHECKING",
        currency="EUR",
        initial_balance=1000,
        initial_balance_date=dt.date(2026, 1, 1),
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


@pytest.fixture()
def usd_account(db: Session, user: User) -> Account:
    account = Account(
        user_id=user.id,
        name="Conta USD",
        account_type="CHECKING",
        currency="USD",
        initial_balance=500,
        initial_balance_date=dt.date(2026, 1, 1),
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


def add_rate(db: Session, base: str, quote: str, rate, on: dt.date) -> None:
    db.add(ExchangeRate(base_code=base, quote_code=quote, rate_date=on, rate=rate, source="MANUAL"))
    db.commit()
