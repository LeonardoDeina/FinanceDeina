import datetime as dt
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.accounts.models import Account
from app.closings.service import ClosingAlreadyClosedError, close_month, reopen_month
from app.transactions.models import Transaction
from app.users.models import User


def _add_transaction(db, user, account, *, ttype, planned=None, actual=None, planned_date=None, actual_date=None, status):
    db.add(
        Transaction(
            user_id=user.id, account_id=account.id, transaction_type=ttype, status=status,
            description="t", currency=account.currency, planned_amount=planned, actual_amount=actual,
            planned_date=planned_date, actual_date=actual_date, source_type="MANUAL",
        )
    )


def test_close_month_computes_planned_vs_actual_and_locks(db: Session, user: User, eur_account: Account):
    _add_transaction(db, user, eur_account, ttype="INCOME", planned=Decimal("3500.00"), planned_date=dt.date(2026, 1, 5), status="PLANNED")
    _add_transaction(db, user, eur_account, ttype="INCOME", actual=Decimal("3500.00"), actual_date=dt.date(2026, 1, 5), status="CLEARED")
    _add_transaction(db, user, eur_account, ttype="EXPENSE", planned=Decimal("2550.00"), planned_date=dt.date(2026, 1, 10), status="PLANNED")
    _add_transaction(db, user, eur_account, ttype="EXPENSE", actual=Decimal("2730.00"), actual_date=dt.date(2026, 1, 10), status="CLEARED")
    db.commit()

    closing = close_month(db, user, dt.date(2026, 1, 1))

    assert closing.status == "CLOSED"
    assert closing.planned_savings == Decimal("950.00")
    assert closing.actual_savings == Decimal("770.00")
    assert closing.closed_at is not None


def test_closing_twice_raises(db: Session, user: User, eur_account: Account):
    close_month(db, user, dt.date(2026, 1, 1))
    with pytest.raises(ClosingAlreadyClosedError):
        close_month(db, user, dt.date(2026, 1, 1))


def test_reopen_records_reason(db: Session, user: User, eur_account: Account):
    close_month(db, user, dt.date(2026, 1, 1))
    reopened = reopen_month(db, user, dt.date(2026, 1, 1), "Encontrei uma nota fiscal atrasada")
    assert reopened.status == "REOPENED"
    assert reopened.reopen_reason == "Encontrei uma nota fiscal atrasada"
