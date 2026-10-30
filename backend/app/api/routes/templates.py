from __future__ import annotations

from math import ceil
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.template import Template
from app.models.user import User
from app.schemas.order import ResponseEnvelope
from app.schemas.template import (
    DeletedTemplate,
    TemplateCreate,
    TemplatePage,
    TemplateRead,
    TemplateUpdate,
)
from app.services.templates import (
    create_template,
    delete_template,
    get_template,
    list_templates,
    update_template,
)

router = APIRouter()
Db = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


def response(data, message: str = "success") -> dict:  # type: ignore[no-untyped-def]
    return {"code": 0, "message": message, "data": data}


def find_template(db: Session, user_id: int, template_id: int) -> Template:
    item = get_template(db, user_id, template_id)
    if item is None:
        raise HTTPException(404, "模板不存在")
    return item


@router.get("", response_model=ResponseEnvelope[TemplatePage], summary="查询模板")
def index(
    db: Db,
    current_user: CurrentUser,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 10,
    keyword: Annotated[str | None, Query(max_length=100)] = None,
) -> dict:
    items, total = list_templates(
        db, current_user.id, page=page, page_size=page_size, keyword=keyword
    )
    return response(
        TemplatePage(
            items=[TemplateRead.model_validate(item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=ceil(total / page_size) if total else 0,
        )
    )


@router.post("", status_code=201, response_model=ResponseEnvelope[TemplateRead], summary="新增模板")
def create(payload: TemplateCreate, db: Db, current_user: CurrentUser) -> dict:
    try:
        item = create_template(db, current_user.id, payload)
    except IntegrityError as exc:
        raise HTTPException(409, "模板名称已存在") from exc
    return response(TemplateRead.model_validate(item), "模板新增成功")


@router.get("/{template_id}", response_model=ResponseEnvelope[TemplateRead], summary="模板详情")
def detail(template_id: int, db: Db, current_user: CurrentUser) -> dict:
    return response(TemplateRead.model_validate(find_template(db, current_user.id, template_id)))


@router.patch("/{template_id}", response_model=ResponseEnvelope[TemplateRead], summary="修改模板")
def edit(template_id: int, payload: TemplateUpdate, db: Db, current_user: CurrentUser) -> dict:
    item = find_template(db, current_user.id, template_id)
    try:
        item = update_template(db, item, payload)
    except IntegrityError as exc:
        raise HTTPException(409, "模板名称已存在") from exc
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    return response(TemplateRead.model_validate(item), "模板修改成功")


@router.delete(
    "/{template_id}", response_model=ResponseEnvelope[DeletedTemplate], summary="删除模板"
)
def remove(template_id: int, db: Db, current_user: CurrentUser) -> dict:
    delete_template(db, find_template(db, current_user.id, template_id))
    return response(DeletedTemplate(deleted_id=template_id), "模板删除成功")
