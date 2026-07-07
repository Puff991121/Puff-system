from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.account_data import AccountDataField, AccountDataRecord
from app.schemas.account_data import FieldCreate, FieldUpdate, Summary

SHANGHAI = ZoneInfo("Asia/Shanghai")
SYSTEM_FIELDS = (
    ("account", "账号", "text"),
    ("followers", "粉丝", "number"),
    ("notes", "发布笔记数", "number"),
)


def now() -> datetime:
    return datetime.now(SHANGHAI)


def ensure_system_fields(db: Session, user_id: int) -> None:
    existing = set(
        db.scalars(select(AccountDataField.field_key).where(AccountDataField.user_id == user_id))
    )
    if all(key in existing for key, _, _ in SYSTEM_FIELDS):
        return
    timestamp = now()
    for order, (key, label, field_type) in enumerate(SYSTEM_FIELDS, 1):
        if key not in existing:
            db.add(
                AccountDataField(
                    user_id=user_id,
                    field_key=key,
                    label=label,
                    field_type=field_type,
                    is_system=True,
                    sort_order=order,
                    created_at=timestamp,
                    updated_at=timestamp,
                )
            )
    db.commit()


def fields(db: Session, user_id: int) -> list[AccountDataField]:
    ensure_system_fields(db, user_id)
    return list(
        db.scalars(
            select(AccountDataField)
            .where(AccountDataField.user_id == user_id)
            .order_by(AccountDataField.sort_order, AccountDataField.id)
        )
    )


def records(db: Session, user_id: int) -> list[AccountDataRecord]:
    return list(
        db.scalars(
            select(AccountDataRecord)
            .where(AccountDataRecord.user_id == user_id)
            .order_by(AccountDataRecord.sort_order, AccountDataRecord.id)
        )
    )


def summary(db: Session, user_id: int) -> Summary:
    items = records(db, user_id)
    return Summary(
        account_count=len(items),
        total_followers=sum(int(item.values_json.get("followers", 0)) for item in items),
        total_notes=sum(int(item.values_json.get("notes", 0)) for item in items),
        field_count=len(fields(db, user_id)),
        updated_at=now(),
    )


def validate_values(
    definitions: list[AccountDataField], values: dict[str, Any], partial: bool
) -> dict[str, Any]:
    by_key = {field.field_key: field for field in definitions}
    unknown = set(values) - set(by_key)
    if unknown:
        raise ValueError(f"字段 {sorted(unknown)[0]} 不存在")
    result = dict(values)
    if not partial:
        result.setdefault("followers", 0)
        result.setdefault("notes", 0)
        for field in definitions:
            result.setdefault(field.field_key, 0 if field.field_type == "number" else "")
    for key, value in result.items():
        field = by_key[key]
        if field.field_type == "number" and (
            isinstance(value, bool) or not isinstance(value, int) or value < 0
        ):
            raise ValueError(f"字段 {key} 必须是非负整数")
        if field.field_type == "text" and not isinstance(value, str):
            raise ValueError(f"字段 {key} 必须是字符串")
    if not partial:
        account = result.get("account", "").strip()
        if not 1 <= len(account) <= 100:
            raise ValueError("字段 account 长度必须为 1～100")
        result["account"] = account
    elif "account" in result:
        account = result["account"].strip()
        if not 1 <= len(account) <= 100:
            raise ValueError("字段 account 长度必须为 1～100")
        result["account"] = account
    return result


def create_record(db: Session, user_id: int, values: dict[str, Any]) -> AccountDataRecord:
    definitions = fields(db, user_id)
    if (
        db.scalar(
            select(func.count(AccountDataRecord.id)).where(AccountDataRecord.user_id == user_id)
        )
        >= 1000
    ):
        raise ValueError("账号记录最多 1000 条")
    timestamp = now()
    maximum = (
        db.scalar(
            select(func.max(AccountDataRecord.sort_order)).where(
                AccountDataRecord.user_id == user_id
            )
        )
        or 0
    )
    item = AccountDataRecord(
        user_id=user_id,
        values_json=validate_values(definitions, values, False),
        sort_order=int(maximum) + 1,
        created_at=timestamp,
        updated_at=timestamp,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def update_record(
    db: Session,
    item: AccountDataRecord,
    definitions: list[AccountDataField],
    values: dict[str, Any],
) -> AccountDataRecord:
    merged = dict(item.values_json)
    merged.update(validate_values(definitions, values, True))
    item.values_json = merged
    item.updated_at = now()
    db.commit()
    db.refresh(item)
    return item


def create_field(db: Session, user_id: int, payload: FieldCreate) -> AccountDataField:
    definitions = fields(db, user_id)
    if len(definitions) >= 30:
        raise ValueError("字段最多 30 个")
    timestamp = now()
    maximum = max((field.sort_order for field in definitions), default=0)
    item = AccountDataField(
        user_id=user_id,
        field_key="pending",
        label=payload.label,
        field_type=payload.type,
        is_system=False,
        sort_order=maximum + 1,
        created_at=timestamp,
        updated_at=timestamp,
    )
    db.add(item)
    db.flush()
    item.field_key = f"custom_{item.id}"
    default = 0 if payload.type == "number" else ""
    for record in records(db, user_id):
        values = dict(record.values_json)
        values[item.field_key] = default
        record.values_json = values
        record.updated_at = timestamp
    db.commit()
    db.refresh(item)
    return item


def update_field(db: Session, item: AccountDataField, payload: FieldUpdate) -> AccountDataField:
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    item.updated_at = now()
    db.commit()
    db.refresh(item)
    return item


def delete_field(db: Session, item: AccountDataField) -> str:
    key = item.field_key
    timestamp = now()
    for record in records(db, item.user_id):
        values = dict(record.values_json)
        values.pop(key, None)
        record.values_json = values
        record.updated_at = timestamp
    db.delete(item)
    db.commit()
    return key
