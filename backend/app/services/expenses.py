from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.models.expense import Expense
from app.schemas.expense import ExpenseCreate, ExpenseUpdate

SHANGHAI = ZoneInfo("Asia/Shanghai")
SORT_FIELDS = {
    "transaction_time": Expense.transaction_time,
    "amount": Expense.amount,
    "created_at": Expense.created_at,
}


def now() -> datetime:
    return datetime.now(SHANGHAI)


def filtered_expenses_query(
    user_id: int,
    *,
    transaction_type: str | None = None,
    description: str | None = None,
    payment_method: str | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
) -> Select:
    statement = select(Expense).where(Expense.user_id == user_id)
    if transaction_type:
        statement = statement.where(Expense.transaction_type == transaction_type.strip())
    if description:
        statement = statement.where(Expense.description.like(f"%{description.strip()}%"))
    if payment_method:
        statement = statement.where(Expense.payment_method == payment_method.strip())
    if start_time:
        statement = statement.where(Expense.transaction_time >= start_time)
    if end_time:
        statement = statement.where(Expense.transaction_time <= end_time)
    return statement


def list_expenses(
    db: Session,
    user_id: int,
    *,
    page: int,
    page_size: int,
    sort_by: str,
    sort_order: str,
    **filters,
):
    base = filtered_expenses_query(user_id, **filters)
    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0
    field = SORT_FIELDS[sort_by]
    order = field.asc() if sort_order == "asc" else field.desc()
    items = db.scalars(
        base.order_by(order, Expense.id.desc()).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return list(items), total


def get_expense(db: Session, user_id: int, expense_id: int):
    return db.scalar(select(Expense).where(Expense.id == expense_id, Expense.user_id == user_id))


def new_expense(user_id: int, payload: ExpenseCreate) -> Expense:
    values = payload.model_dump()
    timestamp = now()
    return Expense(user_id=user_id, created_at=timestamp, updated_at=timestamp, **values)


def create_expense(db: Session, user_id: int, payload: ExpenseCreate) -> Expense:
    expense = new_expense(user_id, payload)
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense


def update_expense(db: Session, expense: Expense, payload: ExpenseUpdate) -> Expense:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(expense, field, value)
    expense.updated_at = now()
    db.commit()
    db.refresh(expense)
    return expense


def delete_expense(db: Session, expense: Expense) -> None:
    db.delete(expense)
    db.commit()


def get_summary(db: Session, user_id: int, reference_date: date | None = None) -> dict:
    current = now()
    today_start = current.replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow_start = today_start + timedelta(days=1)
    period = reference_date or current.date()
    month_start = current.replace(
        year=period.year,
        month=period.month,
        day=1,
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )
    next_month_start = (
        month_start.replace(year=month_start.year + 1, month=1)
        if month_start.month == 12
        else month_start.replace(month=month_start.month + 1)
    )
    year_start = current.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    previous_month_start = (
        month_start.replace(year=month_start.year - 1, month=12)
        if month_start.month == 1
        else month_start.replace(month=month_start.month - 1)
    )
    previous_year_start = year_start.replace(year=year_start.year - 1)

    def aggregate(start: datetime | None = None, end: datetime | None = None):
        filters = [Expense.user_id == user_id]
        if start is not None:
            filters.append(Expense.transaction_time >= start)
        if end is not None:
            filters.append(Expense.transaction_time < end)
        amount, count = db.execute(
            select(func.coalesce(func.sum(Expense.amount), 0), func.count(Expense.id)).where(
                *filters
            )
        ).one()
        return Decimal(amount), int(count)

    def change_rate(current_amount: Decimal, previous_amount: Decimal) -> Decimal | None:
        if previous_amount == 0:
            return Decimal("0") if current_amount == 0 else None
        return ((current_amount - previous_amount) / previous_amount * 100).quantize(
            Decimal("0.01")
        )

    today_amount, today_count = aggregate(today_start, tomorrow_start)
    month_amount, month_count = aggregate(month_start, next_month_start)
    previous_month_amount, _ = aggregate(previous_month_start, month_start)
    year_amount, year_count = aggregate(year_start)
    previous_year_amount, _ = aggregate(previous_year_start, year_start)
    total_amount, total_count = aggregate()
    return {
        "today_amount": today_amount,
        "today_count": today_count,
        "month_amount": month_amount,
        "month_count": month_count,
        "month_change_rate": change_rate(month_amount, previous_month_amount),
        "year_amount": year_amount,
        "year_count": year_count,
        "year_change_rate": change_rate(year_amount, previous_year_amount),
        "total_amount": total_amount,
        "total_count": total_count,
    }
