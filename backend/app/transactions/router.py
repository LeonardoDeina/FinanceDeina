import csv
import datetime as dt
import io

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.accounts.models import Account
from app.audit import service as audit_service
from app.categories.models import Category
from app.db.session import get_db
from app.transactions.models import Tag, Transaction
from app.transactions.schemas import TransactionCreate, TransactionRead, TransactionUpdate, TransferCreate, TransferRead
from app.transactions.service import build_transfer
from app.users.service import get_or_create_profile

router = APIRouter(tags=["transactions"])


def _get_account_or_404(db: Session, account_id: int, user_id: int) -> Account:
    account = db.get(Account, account_id)
    if account is None or account.user_id != user_id:
        raise HTTPException(status_code=404, detail="Conta não encontrada.")
    return account


def _resolve_tags(db: Session, user_id: int, names: list[str]) -> list[Tag]:
    tags = []
    for raw_name in names:
        name = raw_name.strip()
        if not name:
            continue
        tag = db.execute(select(Tag).where(Tag.user_id == user_id, Tag.name == name)).scalar_one_or_none()
        if tag is None:
            tag = Tag(user_id=user_id, name=name)
            db.add(tag)
            db.flush()
        tags.append(tag)
    return tags


_TRANSACTION_FIELDS = [name for name in TransactionRead.model_fields if name != "tags"]


def _to_read(transaction: Transaction) -> TransactionRead:
    data = {field: getattr(transaction, field) for field in _TRANSACTION_FIELDS}
    data["tags"] = [tag.name for tag in transaction.tags]
    return TransactionRead(**data)


@router.get("/transactions", response_model=list[TransactionRead])
def list_transactions(
    account_id: int | None = None,
    category_id: int | None = None,
    status_filter: str | None = None,
    start_date: dt.date | None = None,
    end_date: dt.date | None = None,
    db: Session = Depends(get_db),
):
    profile = get_or_create_profile(db)
    query = select(Transaction).where(Transaction.user_id == profile.id)
    if account_id:
        query = query.where(Transaction.account_id == account_id)
    if category_id:
        query = query.where(Transaction.category_id == category_id)
    if status_filter:
        query = query.where(Transaction.status == status_filter.upper())
    if start_date:
        query = query.where(
            ((Transaction.planned_date.is_not(None)) & (Transaction.planned_date >= start_date))
            | ((Transaction.actual_date.is_not(None)) & (Transaction.actual_date >= start_date))
        )
    if end_date:
        query = query.where(
            ((Transaction.planned_date.is_not(None)) & (Transaction.planned_date <= end_date))
            | ((Transaction.actual_date.is_not(None)) & (Transaction.actual_date <= end_date))
        )
    transactions = list(db.execute(query.order_by(Transaction.id.desc())).scalars())
    return [_to_read(t) for t in transactions]


@router.post("/transactions", response_model=TransactionRead, status_code=201)
def create_transaction(payload: TransactionCreate, db: Session = Depends(get_db)):
    profile = get_or_create_profile(db)
    account = _get_account_or_404(db, payload.account_id, profile.id)

    if payload.category_id is not None:
        category = db.get(Category, payload.category_id)
        if category is None or category.user_id != profile.id:
            raise HTTPException(status_code=404, detail="Categoria não encontrada.")

    transaction = Transaction(
        user_id=profile.id,
        account_id=account.id,
        category_id=payload.category_id,
        transaction_type=payload.transaction_type.upper(),
        status=payload.status.upper(),
        description=payload.description,
        currency=(payload.currency or account.currency).upper(),
        planned_amount=payload.planned_amount,
        actual_amount=payload.actual_amount,
        planned_date=payload.planned_date,
        actual_date=payload.actual_date,
        source_type=payload.source_type.upper(),
        notes=payload.notes,
        tags=_resolve_tags(db, profile.id, payload.tags),
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    audit_service.record(
        db, user_id=profile.id, entity_type="transaction", entity_id=transaction.id, action="CREATE",
        after={"description": transaction.description, "status": transaction.status},
    )
    db.commit()
    return _to_read(transaction)


@router.patch("/transactions/{transaction_id}", response_model=TransactionRead)
def update_transaction(transaction_id: int, payload: TransactionUpdate, db: Session = Depends(get_db)):
    profile = get_or_create_profile(db)
    transaction = db.get(Transaction, transaction_id)
    if transaction is None or transaction.user_id != profile.id:
        raise HTTPException(status_code=404, detail="Transação não encontrada.")

    before = {"status": transaction.status, "actual_amount": str(transaction.actual_amount)}
    data = payload.model_dump(exclude_unset=True, exclude={"tags"})
    for field, value in data.items():
        setattr(transaction, field, value.upper() if field == "status" and value else value)
    if payload.tags is not None:
        transaction.tags = _resolve_tags(db, profile.id, payload.tags)

    db.commit()
    db.refresh(transaction)
    audit_service.record(
        db, user_id=profile.id, entity_type="transaction", entity_id=transaction.id, action="UPDATE",
        before=before, after={"status": transaction.status, "actual_amount": str(transaction.actual_amount)},
    )
    db.commit()
    return _to_read(transaction)


@router.get("/transactions/export.csv")
def export_transactions_csv(
    account_id: int | None = None,
    start_date: dt.date | None = None,
    end_date: dt.date | None = None,
    db: Session = Depends(get_db),
):
    """BKP-003: exported rows always respect the same filters as the list endpoint."""
    profile = get_or_create_profile(db)
    query = select(Transaction).where(Transaction.user_id == profile.id)
    if account_id:
        query = query.where(Transaction.account_id == account_id)
    if start_date:
        query = query.where((Transaction.actual_date >= start_date) | (Transaction.planned_date >= start_date))
    if end_date:
        query = query.where((Transaction.actual_date <= end_date) | (Transaction.planned_date <= end_date))
    transactions = list(db.execute(query.order_by(Transaction.id)).scalars())

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        ["id", "account_id", "category_id", "type", "status", "description", "currency", "planned_amount", "actual_amount", "planned_date", "actual_date", "source_type", "tags"]
    )
    for t in transactions:
        writer.writerow(
            [t.id, t.account_id, t.category_id, t.transaction_type, t.status, t.description, t.currency, t.planned_amount, t.actual_amount, t.planned_date, t.actual_date, t.source_type, "|".join(tag.name for tag in t.tags)]
        )
    buffer.seek(0)
    return StreamingResponse(
        buffer, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=transactions.csv"}
    )


@router.post("/transfers", response_model=TransferRead, status_code=201)
def create_transfer(payload: TransferCreate, db: Session = Depends(get_db)):
    profile = get_or_create_profile(db)
    source = _get_account_or_404(db, payload.source_account_id, profile.id)
    destination = _get_account_or_404(db, payload.destination_account_id, profile.id)

    transfer = build_transfer(
        db,
        user_id=profile.id,
        source_account=source,
        destination_account=destination,
        amount=payload.amount,
        transfer_date=payload.transfer_date,
        description=payload.description,
        bridge_code=profile.base_currency,
    )
    db.add(transfer)
    db.commit()
    db.refresh(transfer)
    audit_service.record(
        db, user_id=profile.id, entity_type="account_transfer", entity_id=transfer.id, action="CREATE",
        after={"amount": str(transfer.amount), "source_currency": transfer.source_currency, "destination_currency": transfer.destination_currency},
    )
    db.commit()
    return transfer
