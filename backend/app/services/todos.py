from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

from sqlalchemy import Select, case, func, select
from sqlalchemy.orm import Session

from app.models.todo import Todo
from app.schemas.todo import TodoCreate, TodoUpdate

SHANGHAI = ZoneInfo("Asia/Shanghai")


def now() -> datetime:
    return datetime.now(SHANGHAI)


def filtered_todos_query(
    user_id: int,
    *,
    period_type: str | None = None,
    status: str | None = None,
    keyword: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> Select:
    statement = select(Todo).where(Todo.user_id == user_id)
    if period_type:
        statement = statement.where(Todo.period_type == period_type)
    if status:
        statement = statement.where(Todo.status == status)
    if keyword and keyword.strip():
        value = f"%{keyword.strip()}%"
        statement = statement.where(
            Todo.title.like(value) | func.coalesce(Todo.description, "").like(value)
        )
    if start_date:
        statement = statement.where(Todo.scheduled_date >= start_date)
    if end_date:
        statement = statement.where(Todo.scheduled_date <= end_date)
    return statement


def list_todos(db: Session, user_id: int, *, page: int, page_size: int, **filters):
    base = filtered_todos_query(user_id, **filters)
    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0
    status_order = case((Todo.status == "pending", 0), else_=1)
    priority_order = case((Todo.priority == "high", 0), (Todo.priority == "medium", 1), else_=2)
    items = db.scalars(
        base.order_by(status_order, Todo.scheduled_date.asc(), priority_order, Todo.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return list(items), int(total)


def get_todo(db: Session, user_id: int, todo_id: int) -> Todo | None:
    return db.scalar(select(Todo).where(Todo.id == todo_id, Todo.user_id == user_id))


def create_todo(db: Session, user_id: int, payload: TodoCreate) -> Todo:
    timestamp = now()
    values = payload.model_dump()
    todo = Todo(
        user_id=user_id,
        completed_at=timestamp if payload.status == "completed" else None,
        created_at=timestamp,
        updated_at=timestamp,
        **values,
    )
    db.add(todo)
    db.commit()
    db.refresh(todo)
    return todo


def update_todo(db: Session, todo: Todo, payload: TodoUpdate) -> Todo:
    values = payload.model_dump(exclude_unset=True)
    if "status" in values and values["status"] != todo.status:
        todo.completed_at = now() if values["status"] == "completed" else None
    for field, value in values.items():
        setattr(todo, field, value)
    todo.updated_at = now()
    db.commit()
    db.refresh(todo)
    return todo


def delete_todo(db: Session, todo: Todo) -> None:
    db.delete(todo)
    db.commit()


def get_summary(db: Session, user_id: int) -> dict[str, int]:
    today = now().date()
    rows = db.execute(
        select(Todo.period_type, Todo.status, Todo.scheduled_date).where(Todo.user_id == user_id)
    ).all()
    total = len(rows)
    completed = sum(row.status == "completed" for row in rows)
    return {
        "total": total,
        "pending": total - completed,
        "completed": completed,
        "overdue": sum(row.status == "pending" and row.scheduled_date < today for row in rows),
        "daily": sum(row.period_type == "daily" for row in rows),
        "weekly": sum(row.period_type == "weekly" for row in rows),
        "monthly": sum(row.period_type == "monthly" for row in rows),
        "completion_rate": round(completed / total * 100) if total else 0,
    }
