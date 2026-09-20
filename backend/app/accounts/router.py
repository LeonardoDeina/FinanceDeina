import datetime as dt

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.accounts.models import Account
from app.accounts.schemas import AccountBalanceAdjustment, AccountCreate, AccountRead, AccountUpdate, AccountWithBalance
from app.audit import service as audit_service
from app.db.session import get_db
from app.reports.aggregation import account_balances
from app.transactions.models import Transaction
from app.transactions.service import account_balance
from app.users.service import get_or_create_profile

router = APIRouter(prefix="/accounts", tags=["accounts"])


def _get_account_or_404(db: Session, account_id: int, user_id: int) -> Account:
    account = db.get(Account, account_id)
    if account is None or account.user_id != user_id:
        raise HTTPException(status_code=404, detail="Conta não encontrada.")
    return account


def _to_account_with_balance(account: Account, balance, balance_in_base_currency, base_currency: str) -> AccountWithBalance:
    return AccountWithBalance(
        **AccountRead.model_validate(account).model_dump(),
        balance=balance,
        balance_in_base_currency=balance_in_base_currency,
        base_currency=base_currency,
    )


@router.get("", response_model=list[AccountWithBalance])
def list_accounts(include_archived: bool = False, as_of: dt.date | None = None, db: Session = Depends(get_db)):
    profile = get_or_create_profile(db)
    target_date = as_of or dt.date.today()
    query = select(Account).where(Account.user_id == profile.id)
    if not include_archived:
        query = query.where(Account.is_active.is_(True))
    accounts = list(db.execute(query.order_by(Account.name)).scalars())

    views = account_balances(db, accounts, profile.base_currency, target_date)
    return [_to_account_with_balance(v.account, v.balance, v.balance_in_base_currency, profile.base_currency) for v in views]


@router.post("", response_model=AccountRead, status_code=201)
def create_account(payload: AccountCreate, db: Session = Depends(get_db)):
    profile = get_or_create_profile(db)
    account = Account(
        user_id=profile.id,
        name=payload.name,
        account_type=payload.account_type.upper(),
        currency=payload.currency.upper(),
        initial_balance=payload.initial_balance,
        initial_balance_date=payload.initial_balance_date,
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    audit_service.record(db, user_id=profile.id, entity_type="account", entity_id=account.id, action="CREATE", after={"name": account.name})
    db.commit()
    return account


@router.patch("/{account_id}", response_model=AccountRead)
def update_account(account_id: int, payload: AccountUpdate, db: Session = Depends(get_db)):
    profile = get_or_create_profile(db)
    account = _get_account_or_404(db, account_id, profile.id)
    before = {"name": account.name, "is_active": account.is_active}
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(account, field, value)
    db.commit()
    db.refresh(account)
    audit_service.record(
        db, user_id=profile.id, entity_type="account", entity_id=account.id, action="UPDATE", before=before,
        after={"name": account.name, "is_active": account.is_active},
    )
    db.commit()
    return account


@router.post("/{account_id}/balance-adjustment", response_model=AccountWithBalance)
def adjust_balance(account_id: int, payload: AccountBalanceAdjustment, db: Session = Depends(get_db)):
    """ACC-004: an explicit, traceable correction — never a silent history rewrite."""
    profile = get_or_create_profile(db)
    account = _get_account_or_404(db, account_id, profile.id)
    current_balance = account_balance(db, account, payload.as_of)
    delta = payload.new_balance - current_balance

    adjustment = Transaction(
        user_id=profile.id,
        account_id=account.id,
        category_id=None,
        transaction_type="INCOME" if delta >= 0 else "EXPENSE",
        status="CLEARED",
        description=f"Ajuste de saldo: {payload.reason}",
        currency=account.currency,
        actual_amount=abs(delta),
        actual_date=payload.as_of,
        source_type="SYSTEM",
        notes=payload.reason,
    )
    db.add(adjustment)
    db.commit()
    audit_service.record(
        db, user_id=profile.id, entity_type="account", entity_id=account.id, action="BALANCE_ADJUSTMENT",
        before={"balance": str(current_balance)}, after={"balance": str(payload.new_balance), "reason": payload.reason},
    )
    db.commit()

    view = account_balances(db, [account], profile.base_currency, payload.as_of)[0]
    return _to_account_with_balance(account, view.balance, view.balance_in_base_currency, profile.base_currency)
