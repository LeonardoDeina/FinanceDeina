import datetime as dt
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.accounts.models import Account
from app.core.money import quantize_money
from app.currency import service as currency_service
from app.transactions.models import AccountTransfer

REALIZED_STATUS = "CLEARED"


def account_balance(db: Session, account: Account, as_of: dt.date) -> Decimal:
    """Saldo derivado do saldo inicial + movimentações realizadas (ACC-003).

    Only CLEARED transactions and committed transfers count; PLANNED/PENDING
    items never touch the real balance, and transfers move money between
    the user's own accounts without becoming income or expense (RB-004).
    """
    from app.transactions.models import Transaction  # local import avoids a cycle at module load

    balance = account.initial_balance if account.initial_balance_date <= as_of else Decimal("0.00")

    income_sum = db.execute(
        select(func.coalesce(func.sum(Transaction.actual_amount), 0)).where(
            Transaction.account_id == account.id,
            Transaction.status == REALIZED_STATUS,
            Transaction.transaction_type == "INCOME",
            Transaction.actual_date.is_not(None),
            Transaction.actual_date <= as_of,
        )
    ).scalar_one()
    expense_sum = db.execute(
        select(func.coalesce(func.sum(Transaction.actual_amount), 0)).where(
            Transaction.account_id == account.id,
            Transaction.status == REALIZED_STATUS,
            Transaction.transaction_type == "EXPENSE",
            Transaction.actual_date.is_not(None),
            Transaction.actual_date <= as_of,
        )
    ).scalar_one()
    transfers_in = db.execute(
        select(func.coalesce(func.sum(AccountTransfer.destination_amount), 0)).where(
            AccountTransfer.destination_account_id == account.id,
            AccountTransfer.transfer_date <= as_of,
        )
    ).scalar_one()
    transfers_out = db.execute(
        select(func.coalesce(func.sum(AccountTransfer.amount), 0)).where(
            AccountTransfer.source_account_id == account.id,
            AccountTransfer.transfer_date <= as_of,
        )
    ).scalar_one()

    return quantize_money(
        Decimal(balance) + Decimal(income_sum) - Decimal(expense_sum) + Decimal(transfers_in) - Decimal(transfers_out)
    )


def build_transfer(
    db: Session,
    *,
    user_id: int,
    source_account: Account,
    destination_account: Account,
    amount: Decimal,
    transfer_date: dt.date,
    description: str | None,
    bridge_code: str,
    source_type: str = "MANUAL",
) -> AccountTransfer:
    """Cross-currency transfers are handled explicitly (spec 18.3 edge case)
    instead of being blocked: the exchange rate on the transfer date decides
    how much lands in the destination account's own currency.
    """
    if source_account.currency == destination_account.currency:
        rate = Decimal("1")
        destination_amount = quantize_money(amount)
    else:
        rate = currency_service.get_rate(
            db, source_account.currency, destination_account.currency, transfer_date, bridge_code
        )
        destination_amount = quantize_money(amount * rate)

    return AccountTransfer(
        user_id=user_id,
        source_account_id=source_account.id,
        destination_account_id=destination_account.id,
        amount=quantize_money(amount),
        source_currency=source_account.currency,
        destination_amount=destination_amount,
        destination_currency=destination_account.currency,
        exchange_rate=rate,
        transfer_date=transfer_date,
        description=description,
        source_type=source_type,
    )
