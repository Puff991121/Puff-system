from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.template import Template
from app.schemas.template import SHARE_LABELS, TemplateCreate, TemplateUpdate

SHANGHAI = ZoneInfo("Asia/Shanghai")


def list_templates(
    db: Session, user_id: int, *, page: int, page_size: int, keyword: str | None
) -> tuple[list[Template], int]:
    statement = select(Template).where(Template.user_id == user_id)
    if keyword and keyword.strip():
        keyword = keyword.strip()
        statement = statement.where(
            or_(
                Template.name.contains(keyword, autoescape=True),
                Template.notes.contains(keyword, autoescape=True),
            )
        )
    total = db.scalar(select(func.count()).select_from(statement.subquery())) or 0
    items = db.scalars(
        statement.order_by(Template.updated_at.asc(), Template.id.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return list(items), int(total)


def get_template(db: Session, user_id: int, template_id: int) -> Template | None:
    return db.scalar(
        select(Template).where(Template.id == template_id, Template.user_id == user_id)
    )


def create_template(db: Session, user_id: int, payload: TemplateCreate) -> Template:
    timestamp = datetime.now(SHANGHAI)
    item = Template(
        user_id=user_id, created_at=timestamp, updated_at=timestamp, **payload.model_dump()
    )
    db.add(item)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(item)
    return item


def update_template(db: Session, item: Template, payload: TemplateUpdate) -> Template:
    values = payload.model_dump(exclude_unset=True)
    if not any(values.get(field, getattr(item, field)) for field in SHARE_LABELS):
        raise ValueError("请至少保留一项分享内容")
    for field, value in values.items():
        setattr(item, field, value)
    item.updated_at = datetime.now(SHANGHAI)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(item)
    return item


def delete_template(db: Session, item: Template) -> None:
    db.delete(item)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
