import datetime as dt
from decimal import Decimal

from sqlalchemy import CHAR, JSON, Date, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import UTCDateTime, utcnow


class ForecastRun(Base):
    __tablename__ = "forecast_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    run_at: Mapped[dt.datetime] = mapped_column(UTCDateTime, default=utcnow, nullable=False)
    horizon_end: Mapped[dt.date] = mapped_column(Date, nullable=False)
    scenario_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    currency: Mapped[str] = mapped_column(CHAR(3), ForeignKey("currencies.code"), nullable=False)
    assumptions_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    starting_balance: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    projected_ending_balance: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(UTCDateTime, default=utcnow, nullable=False)

    monthly_items: Mapped[list["ForecastMonthlyItem"]] = relationship(
        back_populates="forecast_run", cascade="all, delete-orphan"
    )


class ForecastMonthlyItem(Base):
    __tablename__ = "forecast_monthly_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    forecast_run_id: Mapped[int] = mapped_column(ForeignKey("forecast_runs.id"), nullable=False, index=True)
    reference_month: Mapped[dt.date] = mapped_column(Date, nullable=False)
    projected_income: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    projected_expenses: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    projected_savings: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    projected_end_balance: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    category_breakdown_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    forecast_run: Mapped[ForecastRun] = relationship(back_populates="monthly_items")
