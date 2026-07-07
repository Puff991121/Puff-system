from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4
from zoneinfo import ZoneInfo

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from app.models.order import Order
from app.schemas.order import OrderCreate, OrderUpdate, PaymentMethod

SHANGHAI = ZoneInfo("Asia/Shanghai")
SORT_FIELDS = {
    "order_date": Order.order_date,
    "price": Order.price,
    "created_at": Order.created_at,
}


def now() -> datetime:
    return datetime.now(SHANGHAI)


def make_order_no(order_date: date) -> str:
    return f"PF-{order_date:%Y%m%d}-{uuid4().hex[:8].upper()}"


def filtered_orders_query(
    user_id: int,
    *,
    keyword: str | None = None,
    payment_method: PaymentMethod | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> Select[tuple[Order]]:
    statement = select(Order).where(Order.user_id == user_id)
    if keyword:
        pattern = f"%{keyword.strip()}%"
        statement = statement.where(
            or_(
                Order.order_no.like(pattern),
                Order.requirement.like(pattern),
                Order.template.like(pattern),
                Order.format.like(pattern),
                Order.school.like(pattern),
            )
        )
    if payment_method:
        statement = statement.where(Order.payment_method == payment_method.value)
    if start_date:
        statement = statement.where(Order.order_date >= start_date)
    if end_date:
        statement = statement.where(Order.order_date <= end_date)
    return statement


def apply_sort(statement: Select[tuple[Order]], sort_by: str, sort_order: str):  # type: ignore[no-untyped-def]
    field = SORT_FIELDS[sort_by]
    direction = field.asc() if sort_order == "asc" else field.desc()
    statement = statement.order_by(direction)
    if sort_by == "order_date":
        statement = statement.order_by(Order.created_at.desc())
    return statement


def list_orders(
    db: Session,
    user_id: int,
    *,
    page: int,
    page_size: int,
    keyword: str | None,
    payment_method: PaymentMethod | None,
    start_date: date | None,
    end_date: date | None,
    sort_by: str,
    sort_order: str,
) -> tuple[list[Order], int]:
    base = filtered_orders_query(
        user_id,
        keyword=keyword,
        payment_method=payment_method,
        start_date=start_date,
        end_date=end_date,
    )
    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0
    statement = (
        apply_sort(base, sort_by, sort_order).offset((page - 1) * page_size).limit(page_size)
    )
    return list(db.scalars(statement).all()), total


def get_order_summary(
    db: Session, user_id: int, reference_date: date | None = None
) -> dict[str, Decimal | int]:
    today = now().date()
    period_date = reference_date or today
    month_start = period_date.replace(day=1)
    next_month = (
        month_start.replace(year=month_start.year + 1, month=1)
        if month_start.month == 12
        else month_start.replace(month=month_start.month + 1)
    )
    month_end = today if reference_date is None else next_month - timedelta(days=1)
    year_start = period_date.replace(month=1, day=1)
    year_end = today if reference_date is None else period_date.replace(month=12, day=31)

    def aggregate(
        start_date: date | None = None, end_date: date | None = None
    ) -> tuple[Decimal, int]:
        filters = [Order.user_id == user_id]
        if start_date is not None:
            filters.append(Order.order_date >= start_date)
        if end_date is not None:
            filters.append(Order.order_date <= end_date)
        amount, count = db.execute(
            select(func.coalesce(func.sum(Order.price), 0), func.count(Order.id)).where(*filters)
        ).one()
        return Decimal(amount), int(count)

    today_amount, today_count = aggregate(today, today)
    month_amount, month_count = aggregate(month_start, month_end)
    year_amount, year_count = aggregate(year_start, year_end)
    total_amount, total_count = aggregate()
    return {
        "today_amount": today_amount,
        "today_count": today_count,
        "month_amount": month_amount,
        "month_count": month_count,
        "year_amount": year_amount,
        "year_count": year_count,
        "total_amount": total_amount,
        "total_count": total_count,
    }


def get_order_trend(db: Session, user_id: int, year: int) -> list[dict[str, Decimal | int]]:
    items: list[dict[str, Decimal | int]] = []
    for month in range(1, 13):
        start = date(year, month, 1)
        end = (
            date(year + 1, 1, 1)
            if month == 12
            else date(year, month + 1, 1)
        )
        amount, count = db.execute(
            select(func.coalesce(func.sum(Order.price), 0), func.count(Order.id)).where(
                Order.user_id == user_id,
                Order.order_date >= start,
                Order.order_date < end,
            )
        ).one()
        items.append({"month": month, "amount": Decimal(amount), "count": int(count)})
    return items


def get_order(db: Session, user_id: int, order_id: int) -> Order | None:
    return db.scalar(select(Order).where(Order.id == order_id, Order.user_id == user_id))


def new_order(user_id: int, payload: OrderCreate) -> Order:
    values = payload.model_dump()
    values["format"] = payload.format.value
    values["payment_method"] = payload.payment_method.value
    timestamp = now()
    return Order(
        user_id=user_id,
        order_no=make_order_no(payload.order_date),
        created_at=timestamp,
        updated_at=timestamp,
        **values,
    )


def create_order(db: Session, user_id: int, payload: OrderCreate) -> Order:
    order = new_order(user_id, payload)
    db.add(order)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(order)
    return order


def update_order(db: Session, order: Order, payload: OrderUpdate) -> Order:
    values = payload.model_dump(exclude_unset=True)
    for field, value in values.items():
        if hasattr(value, "value"):
            value = value.value
        setattr(order, field, value)
    order.updated_at = now()
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(order)
    return order


def delete_order(db: Session, order: Order) -> None:
    db.delete(order)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise


def normalize_price(value: object) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"))
