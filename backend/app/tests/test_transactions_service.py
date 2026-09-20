import datetime as dt
from decimal import Decimal

from sqlalchemy.orm import Session

from app.accounts.models import Account
from app.transactions.models import Transaction
from app.transactions.service import account_balance, build_transfer
from app.tests.conftest import add_rate
from app.users.models import User


def test_balance_only_counts_cleared_transactions(db: Session, eur_account: Account, user: User):
    db.add_all(
        [
            Transaction(
                user_id=user.id,
                account_id=eur_account.id,
                transaction_type="INCOME",
                status="CLEARED",
                description="Salário",
                currency="EUR",
                actual_amount=Decimal("2000.00"),
                actual_date=dt.date(2026, 1, 5),
                source_type="MANUAL",
            ),
            Transaction(
                user_id=user.id,
                account_id=eur_account.id,
                transaction_type="EXPENSE",
                status="CLEARED",
                description="Aluguel",
                currency="EUR",
                actual_amount=Decimal("800.00"),
                actual_date=dt.date(2026, 1, 10),
                source_type="MANUAL",
            ),
            Transaction(
                user_id=user.id,
                account_id=eur_account.id,
                transaction_type="EXPENSE",
                status="PLANNED",
                description="Viagem (ainda não ocorreu)",
                currency="EUR",
                planned_amount=Decimal("500.00"),
                planned_date=dt.date(2026, 1, 20),
                source_type="MANUAL",
            ),
        ]
    )
    db.commit()

    # initial 1000 + 2000 income - 800 expense = 2200; the PLANNED trip never touches the real balance
    assert account_balance(db, eur_account, dt.date(2026, 1, 31)) == Decimal("2200.00")


def test_balance_excludes_transactions_after_as_of_date(db: Session, eur_account: Account, user: User):
    db.add(
        Transaction(
            user_id=user.id,
            account_id=eur_account.id,
            transaction_type="INCOME",
            status="CLEARED",
            description="Salário futuro",
            currency="EUR",
            actual_amount=Decimal("2000.00"),
            actual_date=dt.date(2026, 2, 5),
            source_type="MANUAL",
        )
    )
    db.commit()
    assert account_balance(db, eur_account, dt.date(2026, 1, 31)) == Decimal("1000.00")


def test_transfer_between_same_currency_accounts_has_rate_one(db: Session, user: User, eur_account: Account):
    other = Account(
        user_id=user.id, name="Poupança EUR", account_type="SAVINGS", currency="EUR",
        initial_balance=Decimal("0.00"), initial_balance_date=dt.date(2026, 1, 1),
    )
    db.add(other)
    db.commit()
    db.refresh(other)

    transfer = build_transfer(
        db, user_id=user.id, source_account=eur_account, destination_account=other,
        amount=Decimal("200.00"), transfer_date=dt.date(2026, 1, 10), description="Poupança mensal",
        bridge_code="EUR",
    )
    assert transfer.exchange_rate == Decimal("1")
    assert transfer.destination_amount == Decimal("200.00")


def test_cross_currency_transfer_converts_at_transfer_date_rate(
    db: Session, user: User, eur_account: Account, usd_account: Account
):
    add_rate(db, "EUR", "USD", Decimal("1.10"), dt.date(2026, 1, 1))

    transfer = build_transfer(
        db, user_id=user.id, source_account=eur_account, destination_account=usd_account,
        amount=Decimal("100.00"), transfer_date=dt.date(2026, 1, 15), description="Para conta em dólar",
        bridge_code="EUR",
    )
    assert transfer.source_currency == "EUR"
    assert transfer.destination_currency == "USD"
    assert transfer.destination_amount == Decimal("110.00")


def test_transfers_move_balance_without_becoming_income_or_expense(
    db: Session, user: User, eur_account: Account
):
    other = Account(
        user_id=user.id, name="Poupança EUR", account_type="SAVINGS", currency="EUR",
        initial_balance=Decimal("0.00"), initial_balance_date=dt.date(2026, 1, 1),
    )
    db.add(other)
    db.commit()
    db.refresh(other)

    transfer = build_transfer(
        db, user_id=user.id, source_account=eur_account, destination_account=other,
        amount=Decimal("300.00"), transfer_date=dt.date(2026, 1, 10), description=None, bridge_code="EUR",
    )
    db.add(transfer)
    db.commit()

    assert account_balance(db, eur_account, dt.date(2026, 1, 31)) == Decimal("700.00")
    assert account_balance(db, other, dt.date(2026, 1, 31)) == Decimal("300.00")
