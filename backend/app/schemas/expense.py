from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_serializer,
    field_validator,
    model_validator,
)

from app.schemas.order import SHANGHAI, ResponseEnvelope


class ExpenseFields(BaseModel):
    transaction_time: datetime
    transaction_type: str = Field(min_length=1, max_length=30)
    counterparty: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1, max_length=300)
    amount: Decimal = Field(ge=Decimal("0.01"), max_digits=18, decimal_places=2)
    payment_method: str = Field(min_length=1, max_length=30)

    @field_validator("transaction_type", "counterparty", "description", "payment_method")
    @classmethod
    def strip_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("不能为空")
        return value


class ExpenseCreate(ExpenseFields):
    pass


class ExpenseUpdate(BaseModel):
    transaction_time: datetime | None = None
    transaction_type: str | None = Field(None, min_length=1, max_length=30)
    counterparty: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, min_length=1, max_length=300)
    amount: Decimal | None = Field(None, ge=Decimal("0.01"), max_digits=18, decimal_places=2)
    payment_method: str | None = Field(None, min_length=1, max_length=30)

    @field_validator("transaction_type", "counterparty", "description", "payment_method")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else None

    @model_validator(mode="after")
    def ensure_non_empty(self):
        if not self.model_fields_set:
            raise ValueError("至少需要提供一个修改字段")
        return self


class ExpenseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    transaction_time: datetime
    transaction_type: str
    counterparty: str
    description: str
    amount: Decimal
    payment_method: str
    created_at: datetime
    updated_at: datetime

    @field_serializer("amount")
    def serialize_amount(self, value: Decimal) -> str:
        return f"{value:.2f}"

    @field_serializer("transaction_time", "created_at", "updated_at")
    def serialize_datetime(self, value: datetime) -> str:
        if value.tzinfo is None:
            value = value.replace(tzinfo=SHANGHAI)
        return value.isoformat()


class ExpensePage(BaseModel):
    items: list[ExpenseRead]
    total: int
    page: int
    page_size: int
    total_pages: int


class ExpenseSummary(BaseModel):
    today_amount: Decimal
    today_count: int
    month_amount: Decimal
    month_count: int
    month_change_rate: Decimal | None
    year_amount: Decimal
    year_count: int
    year_change_rate: Decimal | None
    total_amount: Decimal
    total_count: int

    @field_serializer("today_amount", "month_amount", "year_amount", "total_amount")
    def serialize_amount(self, value: Decimal) -> str:
        return f"{value:.2f}"

    @field_serializer("month_change_rate", "year_change_rate")
    def serialize_rate(self, value: Decimal | None) -> str | None:
        return f"{value:.2f}" if value is not None else None


class DeletedExpense(BaseModel):
    deleted_id: int


class ExpenseImportError(BaseModel):
    row: int
    field: str
    value: Any
    message: str


class ExpenseImportResult(BaseModel):
    total_rows: int
    success_count: int
    failed_count: int
    imported_expenses: list[ExpenseRead]
    errors: list[ExpenseImportError]


__all__ = ["ResponseEnvelope"]
