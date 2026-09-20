import datetime as dt
from decimal import Decimal

from sqlalchemy import CHAR, Column, Date, ForeignKey, Numeric, String, Table, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin, UTCDateTime, utcnow

transaction_tags = Table(
    "transaction_tags",
    Base.metadata,
    Column("transaction_id", ForeignKey("transactions.id"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id"), primary_key=True),
)


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(60), nullable=False)


class Transaction(Base, TimestampMixin):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False, index=True)
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), nullable=True, index=True)
    transaction_type: Mapped[str] = mapped_column(String(20), nullable=False)  # INCOME | EXPENSE
    status: Mapped[str] = mapped_column(String(24), nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    currency: Mapped[str] = mapped_column(CHAR(3), ForeignKey("currencies.code"), nullable=False)
    planned_amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    actual_amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    planned_date: Mapped[dt.date | None] = mapped_column(Date, nullable=True, index=True)
    actual_date: Mapped[dt.date | None] = mapped_column(Date, nullable=True, index=True)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    source_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    recurring_rule_id: Mapped[int | None] = mapped_column(ForeignKey("recurring_rules.id"), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    tags: Mapped[list[Tag]] = relationship(secondary=transaction_tags)


class AccountTransfer(Base):
    __tablename__ = "account_transfers"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    source_account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False)
    destination_account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    source_currency: Mapped[str] = mapped_column(CHAR(3), ForeignKey("currencies.code"), nullable=False)
    destination_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    destination_currency: Mapped[str] = mapped_column(CHAR(3), ForeignKey("currencies.code"), nullable=False)
    exchange_rate: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)
    transfer_date: Mapped[dt.date] = mapped_column(Date, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(UTCDateTime, default=utcnow, nullable=False)
