from __future__ import annotations

from datetime import date
from math import ceil
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.order import ResponseEnvelope
from app.schemas.todo import (
    DeletedTodo,
    TodoCreate,
    TodoPage,
    TodoRead,
    TodoSummary,
    TodoUpdate,
)
from app.services.todos import (
    create_todo,
    delete_todo,
    get_summary,
    get_todo,
    list_todos,
    update_todo,
)

router = APIRouter()
Db = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


def response(data, message: str = "success") -> dict:
    return {"code": 0, "message": message, "data": data}


@router.get("", response_model=ResponseEnvelope[TodoPage], summary="查询待办事项")
def index(
    db: Db,
    current_user: CurrentUser,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    period_type: Literal["daily", "weekly", "monthly"] | None = None,
    status: Literal["pending", "completed"] | None = None,
    keyword: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> dict:
    if start_date and end_date and start_date > end_date:
        raise HTTPException(400, "开始日期不能晚于结束日期")
    items, total = list_todos(
        db,
        current_user.id,
        page=page,
        page_size=page_size,
        period_type=period_type,
        status=status,
        keyword=keyword,
        start_date=start_date,
        end_date=end_date,
    )
    return response(
        TodoPage(
            items=[TodoRead.model_validate(item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=ceil(total / page_size) if total else 0,
        )
    )


@router.get("/summary", response_model=ResponseEnvelope[TodoSummary], summary="待办统计")
def summary(db: Db, current_user: CurrentUser) -> dict:
    return response(TodoSummary(**get_summary(db, current_user.id)))


@router.post("", status_code=201, response_model=ResponseEnvelope[TodoRead], summary="新增待办")
def create(payload: TodoCreate, db: Db, current_user: CurrentUser) -> dict:
    return response(TodoRead.model_validate(create_todo(db, current_user.id, payload)), "新增成功")


@router.get("/{todo_id}", response_model=ResponseEnvelope[TodoRead], summary="待办详情")
def detail(todo_id: int, db: Db, current_user: CurrentUser) -> dict:
    item = get_todo(db, current_user.id, todo_id)
    if item is None:
        raise HTTPException(404, "待办事项不存在")
    return response(TodoRead.model_validate(item))


@router.patch("/{todo_id}", response_model=ResponseEnvelope[TodoRead], summary="修改待办")
def edit(todo_id: int, payload: TodoUpdate, db: Db, current_user: CurrentUser) -> dict:
    item = get_todo(db, current_user.id, todo_id)
    if item is None:
        raise HTTPException(404, "待办事项不存在")
    return response(TodoRead.model_validate(update_todo(db, item, payload)), "修改成功")


@router.delete("/{todo_id}", response_model=ResponseEnvelope[DeletedTodo], summary="删除待办")
def remove(todo_id: int, db: Db, current_user: CurrentUser) -> dict:
    item = get_todo(db, current_user.id, todo_id)
    if item is None:
        raise HTTPException(404, "待办事项不存在")
    delete_todo(db, item)
    return response(DeletedTodo(deleted_id=todo_id), "删除成功")
