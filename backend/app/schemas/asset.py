from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Generic, Literal, TypeVar
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
AccountType = Literal["asset", "liability"]


class AssetAccountCreate(BaseModel):
    type: AccountType
    account: str = Field(min_length=1, max_length=30)
    amount: Decimal = Field(max_digits=18, decimal_places=2)

    @field_validator("account")
    @classmethod
    def strip_account(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("账户名称不能为空")
        return value

    @model_validator(mode="after")
    def validate_amount_sign(self) -> AssetAccountCreate:
        if self.type == "asset" and self.amount < 0:
            raise ValueError("资产账户金额不能小于 0")
        if self.type == "liability" and self.amount > 0:
            raise ValueError("负债账户金额不能大于 0")
        return self


class AssetAccountUpdate(BaseModel):
    account: str | None = Field(None, min_length=1, max_length=30)
    amount: Decimal | None = Field(None, max_digits=18, decimal_places=2)
    sort_order: int | None = Field(None, ge=0)

    @field_validator("account")
    @classmethod
    def strip_optional_account(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("账户名称不能为空")
        return value

    @model_validator(mode="after")
    def ensure_non_empty(self) -> AssetAccountUpdate:
        if not self.model_fields_set:
            raise ValueError("至少需要提供一个修改字段")
        return self


class AssetAccountRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: AccountType
    account: str
    amount: Decimal
    sort_order: int
    created_at: datetime
    updated_at: datetime

    @field_serializer("amount")
    def serialize_amount(self, value: Decimal) -> str:
        return f"{value:.2f}"

    @field_serializer("created_at", "updated_at")
    def serialize_datetime(self, value: datetime) -> str:
        if value.tzinfo is None:
            value = value.replace(tzinfo=SHANGHAI)
        return value.isoformat()


class AssetSummary(BaseModel):
    total_assets: Decimal
    total_liabilities: Decimal
    net_assets: Decimal
    liability_ratio: Decimal
    asset_account_count: int
    liability_account_count: int
    updated_at: datetime

    @field_serializer("total_assets", "total_liabilities", "net_assets", "liability_ratio")
    def serialize_decimal(self, value: Decimal) -> str:
        return f"{value:.2f}"


class AssetPageData(BaseModel):
    summary: AssetSummary
    assets: list[AssetAccountRead]
    liabilities: list[AssetAccountRead]


class AssetMutationResult(BaseModel):
    account: AssetAccountRead
    summary: AssetSummary


class AssetDeleteResult(BaseModel):
    deleted_id: int
    summary: AssetSummary


T = TypeVar("T")


class AssetResponse(BaseModel, Generic[T]):
    code: int = 0
    message: str = "success"
    data: T
