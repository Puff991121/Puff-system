from __future__ import annotations

from math import ceil
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.xianyu_link import XianyuLink
from app.schemas.order import ResponseEnvelope
from app.schemas.xianyu_link import (
    DeletedXianyuLink,
    XianyuLinkCreate,
    XianyuLinkPage,
    XianyuLinkRead,
    XianyuLinkUpdate,
)
from app.services.xianyu_links import create_link, delete_link, get_link, list_links, update_link

router = APIRouter()
Db = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


def response(data, message: str = "success") -> dict:  # type: ignore[no-untyped-def]
    return {"code": 0, "message": message, "data": data}


def find_link(db: Session, user_id: int, link_id: int) -> XianyuLink:
    item = get_link(db, user_id, link_id)
    if item is None:
        raise HTTPException(404, "闲鱼链接不存在")
    return item


@router.get("", response_model=ResponseEnvelope[XianyuLinkPage], summary="查询闲鱼链接")
def index(
    db: Db,
    current_user: CurrentUser,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 10,
    keyword: Annotated[str | None, Query(max_length=200)] = None,
) -> dict:
    items, total = list_links(db, current_user.id, page=page, page_size=page_size, keyword=keyword)
    return response(
        XianyuLinkPage(
            items=[XianyuLinkRead.model_validate(item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=ceil(total / page_size) if total else 0,
        )
    )


@router.post(
    "", status_code=201, response_model=ResponseEnvelope[XianyuLinkRead], summary="新增闲鱼链接"
)
def create(payload: XianyuLinkCreate, db: Db, current_user: CurrentUser) -> dict:
    return response(
        XianyuLinkRead.model_validate(create_link(db, current_user.id, payload)), "闲鱼链接新增成功"
    )


@router.get("/{link_id}", response_model=ResponseEnvelope[XianyuLinkRead], summary="闲鱼链接详情")
def detail(link_id: int, db: Db, current_user: CurrentUser) -> dict:
    return response(XianyuLinkRead.model_validate(find_link(db, current_user.id, link_id)))


@router.patch("/{link_id}", response_model=ResponseEnvelope[XianyuLinkRead], summary="修改闲鱼链接")
def edit(link_id: int, payload: XianyuLinkUpdate, db: Db, current_user: CurrentUser) -> dict:
    item = update_link(db, find_link(db, current_user.id, link_id), payload)
    return response(XianyuLinkRead.model_validate(item), "闲鱼链接修改成功")


@router.delete(
    "/{link_id}", response_model=ResponseEnvelope[DeletedXianyuLink], summary="删除闲鱼链接"
)
def remove(link_id: int, db: Db, current_user: CurrentUser) -> dict:
    delete_link(db, find_link(db, current_user.id, link_id))
    return response(DeletedXianyuLink(deleted_id=link_id), "闲鱼链接删除成功")
