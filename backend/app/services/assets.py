from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.asset import AssetAccount
from app.schemas.asset import AssetAccountCreate, AssetAccountUpdate, AssetSummary

SHANGHAI = ZoneInfo("Asia/Shanghai")


def now() -> datetime:
    return datetime.now(SHANGHAI)


def get_accounts(db: Session, user_id: int, account_type: str) -> list[AssetAccount]:
    statement = (
        select(AssetAccount)
        .where(AssetAccount.user_id == user_id, AssetAccount.type == account_type)
        .order_by(AssetAccount.sort_order.asc(), AssetAccount.id.asc())
    )
    return list(db.scalars(statement).all())


def get_account(db: Session, user_id: int, account_id: int) -> AssetAccount | None:
    return db.scalar(
        select(AssetAccount).where(
            AssetAccount.id == account_id,
            AssetAccount.user_id == user_id,
        )
    )


def get_summary(db: Session, user_id: int) -> AssetSummary:
    rows = db.execute(
        select(
            AssetAccount.type,
            func.coalesce(func.sum(AssetAccount.amount), 0),
            func.count(AssetAccount.id),
        )
        .where(AssetAccount.user_id == user_id)
        .group_by(AssetAccount.type)
    ).all()
    totals = {row[0]: (Decimal(row[1]), int(row[2])) for row in rows}
    total_assets, asset_count = totals.get("asset", (Decimal("0"), 0))
    total_liabilities, liability_count = totals.get("liability", (Decimal("0"), 0))
    net_assets = total_assets + total_liabilities
    ratio = (
        (abs(total_liabilities) / total_assets * Decimal("100")) if total_assets else Decimal("0")
    )
    return AssetSummary(
        total_assets=total_assets,
        total_liabilities=total_liabilities,
        net_assets=net_assets,
        liability_ratio=ratio.quantize(Decimal("0.01")),
        asset_account_count=asset_count,
        liability_account_count=liability_count,
        updated_at=now(),
    )


def next_sort_order(db: Session, user_id: int, account_type: str) -> int:
    maximum = db.scalar(
        select(func.max(AssetAccount.sort_order)).where(
            AssetAccount.user_id == user_id,
            AssetAccount.type == account_type,
        )
    )
    return int(maximum or 0) + 1


def create_account(db: Session, user_id: int, payload: AssetAccountCreate) -> AssetAccount:
    timestamp = now()
    account = AssetAccount(
        user_id=user_id,
        type=payload.type,
        account=payload.account,
        amount=payload.amount,
        sort_order=next_sort_order(db, user_id, payload.type),
        created_at=timestamp,
        updated_at=timestamp,
    )
    db.add(account)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise
    db.refresh(account)
    return account


def update_account(db: Session, account: AssetAccount, payload: AssetAccountUpdate) -> AssetAccount:
    values = payload.model_dump(exclude_unset=True)
    amount = values.get("amount")
    if amount is not None:
        if account.type == "asset" and amount < 0:
            raise ValueError("资产账户金额不能小于 0")
        if account.type == "liability" and amount > 0:
            raise ValueError("负债账户金额不能大于 0")
    for field, value in values.items():
        setattr(account, field, value)
    account.updated_at = now()
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise
    db.refresh(account)
    return account


def delete_account(db: Session, account: AssetAccount) -> None:
    db.delete(account)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
