from sqlalchemy import select
from sqlalchemy.orm import Session

from app.currency.models import Currency

DEFAULT_CURRENCIES = [
    ("EUR", "Euro", "€"),
    ("USD", "Dólar americano", "$"),
    ("BRL", "Real brasileiro", "R$"),
    ("GBP", "Libra esterlina", "£"),
    ("CHF", "Franco suíço", "CHF"),
]


def seed_default_currencies(db: Session) -> None:
    """Pre-populates the currencies the user mentioned (EUR/USD/BRL) plus a
    couple more, so accounts can be created immediately without first
    registering every currency by hand."""
    existing = {c for c in db.execute(select(Currency.code)).scalars()}
    for code, name, symbol in DEFAULT_CURRENCIES:
        if code not in existing:
            db.add(Currency(code=code, name=name, symbol=symbol, decimal_places=2))
    db.commit()
