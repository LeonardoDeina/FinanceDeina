import datetime as dt
from decimal import Decimal

from sqlalchemy import JSON, CHAR, Date, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import UTCDateTime


class MonthlyClosing(Base):
    __tablename__ = "monthly_closings"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    reference_month: Mapped[dt.date] = mapped_column(Date, nullable=False, index=True)
    currency: Mapped[str] = mapped_column(CHAR(3), ForeignKey("currencies.code"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="OPEN")
    planned_income: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    actual_income: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    planned_expenses: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    actual_expenses: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    planned_savings: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    actual_savings: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    reconciliation_coverage_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    forecast_run_id: Mapped[int | None] = mapped_column(ForeignKey("forecast_runs.id"), nullable=True)
    reopen_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    closed_at: Mapped[dt.datetime | None] = mapped_column(UTCDateTime, nullable=True)
    snapshot_json: Mapped[dict] = mapped_column(JSON, nullable=False)
