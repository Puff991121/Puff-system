from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.account_data import AccountDataField, AccountDataRecord
from app.models.user import User
from app.schemas.account_data import (
    AccountDataResponse,
    FieldCreate,
    FieldDelete,
    FieldMutation,
    FieldRead,
    FieldUpdate,
    PageData,
    RecordDelete,
    RecordMutation,
    RecordRead,
    RecordValues,
)
from app.services import account_data as service

router = APIRouter()
Db = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


def response(data, message: str = "success") -> dict:  # type: ignore[no-untyped-def]
    return {"code": 0, "message": message, "data": data}


def field_read(item: AccountDataField) -> FieldRead:
    return FieldRead(
        id=item.id,
        key=item.field_key,
        label=item.label,
        type=item.field_type,
        is_system=item.is_system,
        sort_order=item.sort_order,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def record_read(item: AccountDataRecord) -> RecordRead:
    return RecordRead(
        id=item.id,
        values=item.values_json,
        sort_order=item.sort_order,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def record_or_404(db: Session, user_id: int, item_id: int) -> AccountDataRecord:
    item = db.scalar(
        select(AccountDataRecord).where(
            AccountDataRecord.id == item_id, AccountDataRecord.user_id == user_id
        )
    )
    if item is None:
        raise HTTPException(404, "账号记录不存在")
    return item


def field_or_404(db: Session, user_id: int, item_id: int) -> AccountDataField:
    item = db.scalar(
        select(AccountDataField).where(
            AccountDataField.id == item_id, AccountDataField.user_id == user_id
        )
    )
    if item is None:
        raise HTTPException(404, "字段不存在")
    return item


@router.get("", response_model=AccountDataResponse[PageData])
def page(db: Db, current_user: CurrentUser) -> dict:
    definitions = service.fields(db, current_user.id)
    items = service.records(db, current_user.id)
    return response(
        PageData(
            fields=[field_read(x) for x in definitions],
            records=[record_read(x) for x in items],
            summary=service.summary(db, current_user.id),
        )
    )


@router.post("/records", status_code=201, response_model=AccountDataResponse[RecordMutation])
def add_record(payload: RecordValues, db: Db, current_user: CurrentUser) -> dict:
    try:
        item = service.create_record(db, current_user.id, payload.values)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(400, str(exc)) from exc
    return response(
        RecordMutation(record=record_read(item), summary=service.summary(db, current_user.id)),
        "账号新增成功",
    )


@router.patch("/records/{record_id}", response_model=AccountDataResponse[RecordMutation])
def edit_record(record_id: int, payload: RecordValues, db: Db, current_user: CurrentUser) -> dict:
    item = record_or_404(db, current_user.id, record_id)
    try:
        item = service.update_record(db, item, service.fields(db, current_user.id), payload.values)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(400, str(exc)) from exc
    return response(
        RecordMutation(record=record_read(item), summary=service.summary(db, current_user.id)),
        "账号数据更新成功",
    )


@router.delete("/records/{record_id}", response_model=AccountDataResponse[RecordDelete])
def remove_record(record_id: int, db: Db, current_user: CurrentUser) -> dict:
    item = record_or_404(db, current_user.id, record_id)
    db.delete(item)
    db.commit()
    return response(
        RecordDelete(deleted_id=record_id, summary=service.summary(db, current_user.id)),
        "账号删除成功",
    )


@router.post("/fields", status_code=201, response_model=AccountDataResponse[FieldMutation])
def add_field(payload: FieldCreate, db: Db, current_user: CurrentUser) -> dict:
    try:
        item = service.create_field(db, current_user.id, payload)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(400, str(exc)) from exc
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "字段名称已存在") from exc
    default = 0 if item.field_type == "number" else ""
    return response(FieldMutation(field=field_read(item), default_value=default), "字段新增成功")


@router.patch("/fields/{field_id}", response_model=AccountDataResponse[FieldMutation])
def edit_field(field_id: int, payload: FieldUpdate, db: Db, current_user: CurrentUser) -> dict:
    item = field_or_404(db, current_user.id, field_id)
    try:
        item = service.update_field(db, item, payload)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "字段名称已存在") from exc
    return response(FieldMutation(field=field_read(item)), "字段更新成功")


@router.delete("/fields/{field_id}", response_model=AccountDataResponse[FieldDelete])
def remove_field(field_id: int, db: Db, current_user: CurrentUser) -> dict:
    item = field_or_404(db, current_user.id, field_id)
    if item.is_system:
        raise HTTPException(403, "系统字段不允许删除")
    key = service.delete_field(db, item)
    return response(
        FieldDelete(
            deleted_id=field_id, deleted_key=key, summary=service.summary(db, current_user.id)
        ),
        "字段删除成功",
    )
