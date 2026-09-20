import datetime as dt
from decimal import Decimal

from sqlalchemy import CHAR, Date, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import UTCDateTime, utcnow


class Currency(Base):
    """Currencies the user can hold money in (accounts, transactions, goals).

    Multi-currency is a core requirement: the user earns and spends in
    EUR/USD/BRL simultaneously, so every account and transaction carries its
    own currency instead of forcing a single base currency for all values.
    """

    __tablename__ = "currencies"

    code: Mapped[str] = mapped_column(CHAR(3), primary_key=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    symbol: Mapped[str] = mapped_column(String(8), nullable=False)
    decimal_places: Mapped[int] = mapped_column(default=2, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)


class ExchangeRate(Base):
    """Manually maintained rate: 1 unit of base_code == rate units of quote_code.

    Real-time FX is explicitly out of scope for V1 (per spec); rates are
    entered/updated by the user (or a seed script) and the conversion
    service picks the most recent rate on/before the requested date, with a
    bridge through the user's base currency when no direct pair exists.
    """

    __tablename__ = "exchange_rates"
    __table_args__ = (UniqueConstraint("base_code", "quote_code", "rate_date", name="uq_rate_pair_date"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    base_code: Mapped[str] = mapped_column(CHAR(3), ForeignKey("currencies.code"), nullable=False)
    quote_code: Mapped[str] = mapped_column(CHAR(3), ForeignKey("currencies.code"), nullable=False)
    rate_date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    rate: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)
    source: Mapped[str] = mapped_column(String(16), default="MANUAL", nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(UTCDateTime, default=utcnow, nullable=False)
