from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Generic, TypeVar
from zoneinfo import ZoneInfo

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_serializer,
    field_validator,
    model_validator,
)

SHANGHAI = ZoneInfo("Asia/Shanghai")


class OrderFormat(str, Enum):
    FIGMA = "Figma"
    PSD = "Psd"
    XD = "Xd"
    JSD = "Jsd"
    HTML = "Html"
    CUSTOM = "定做"
    NONE = "无"


class PaymentMethod(str, Enum):
    WECHAT = "微信"
    XIAN_YU = "咸鱼"
    RED = "小红书"
    ALIPAY = "支付宝"


class OrderFields(BaseModel):
    order_date: date = Field(default_factory=date.today)
    requirement: str = Field(min_length=1, max_length=500)
    template: str = Field(min_length=1, max_length=100)
    format: OrderFormat
    school: str = Field(min_length=1, max_length=100)
    price: Decimal = Field(ge=Decimal("0.01"), max_digits=18, decimal_places=2)
    payment_method: PaymentMethod

    @field_validator("requirement", "template", "school")
    @classmethod
    def strip_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("不能为空")
        return value


class OrderCreate(OrderFields):
    pass


class OrderUpdate(BaseModel):
    order_date: date | None = None
    requirement: str | None = Field(None, min_length=1, max_length=500)
    template: str | None = Field(None, min_length=1, max_length=100)
    format: OrderFormat | None = None
    school: str | None = Field(None, min_length=1, max_length=100)
    price: Decimal | None = Field(None, ge=Decimal("0.01"), max_digits=18, decimal_places=2)
    payment_method: PaymentMethod | None = None

    @field_validator("requirement", "template", "school")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("不能为空")
        return value

    @model_validator(mode="after")
    def ensure_non_empty(self) -> OrderUpdate:
        if not self.model_fields_set:
            raise ValueError("至少需要提供一个修改字段")
        return self


class OrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_no: str
    order_date: date
    requirement: str
    template: str
    format: OrderFormat
    school: str
    price: Decimal
    payment_method: PaymentMethod
    created_at: datetime
    updated_at: datetime

    @field_serializer("price")
    def serialize_price(self, value: Decimal) -> str:
        return f"{value:.2f}"

    @field_serializer("created_at", "updated_at")
    def serialize_datetime(self, value: datetime) -> str:
        if value.tzinfo is None:
            value = value.replace(tzinfo=SHANGHAI)
        return value.isoformat()


class OrderPage(BaseModel):
    items: list[OrderRead]
    total: int
    page: int
    page_size: int
    total_pages: int


class DeletedOrder(BaseModel):
    deleted_id: int


class ImportErrorItem(BaseModel):
    row: int
    field: str
    value: Any
    message: str


class ImportResult(BaseModel):
    total_rows: int
    success_count: int
    failed_count: int
    imported_orders: list[OrderRead]
    errors: list[ImportErrorItem]


T = TypeVar("T")


class ResponseEnvelope(BaseModel, Generic[T]):
    code: int = 0
    message: str = "success"
    data: T
