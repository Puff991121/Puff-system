from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.xianyu_link import XianyuLink
from app.schemas.xianyu_link import XianyuLinkCreate, XianyuLinkUpdate

SHANGHAI = ZoneInfo("Asia/Shanghai")


def list_links(
    db: Session, user_id: int, *, page: int, page_size: int, keyword: str | None
) -> tuple[list[XianyuLink], int]:
    statement = select(XianyuLink).where(XianyuLink.user_id == user_id)
    if keyword and keyword.strip():
        keyword = keyword.strip()
        statement = statement.where(
            or_(
                XianyuLink.title.contains(keyword, autoescape=True),
                XianyuLink.link.contains(keyword, autoescape=True),
            )
        )
    total = db.scalar(select(func.count()).select_from(statement.subquery())) or 0
    items = db.scalars(
        statement.order_by(XianyuLink.updated_at.asc(), XianyuLink.id.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return list(items), int(total)


def get_link(db: Session, user_id: int, link_id: int) -> XianyuLink | None:
    return db.scalar(
        select(XianyuLink).where(XianyuLink.id == link_id, XianyuLink.user_id == user_id)
    )


def create_link(db: Session, user_id: int, payload: XianyuLinkCreate) -> XianyuLink:
    timestamp = datetime.now(SHANGHAI)
    item = XianyuLink(
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


def update_link(db: Session, item: XianyuLink, payload: XianyuLinkUpdate) -> XianyuLink:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    item.updated_at = datetime.now(SHANGHAI)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(item)
    return item


def delete_link(db: Session, item: XianyuLink) -> None:
    db.delete(item)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
