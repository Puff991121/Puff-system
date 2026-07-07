from __future__ import annotations

from datetime import datetime
from typing import Any, Generic, Literal, TypeVar

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

FieldType = Literal["text", "number"]


class RecordValues(BaseModel):
    values: dict[str, Any]

    @field_validator("values")
    @classmethod
    def values_must_not_be_empty(cls, value: dict[str, Any]) -> dict[str, Any]:
        if not value:
            raise ValueError("至少需要提供一个字段")
        return value


class FieldCreate(BaseModel):
    label: str = Field(min_length=1, max_length=20)
    type: FieldType

    @field_validator("label")
    @classmethod
    def strip_label(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("字段名称不能为空")
        return value


class FieldUpdate(BaseModel):
    label: str | None = Field(None, min_length=1, max_length=20)
    sort_order: int | None = Field(None, ge=0)

    @field_validator("label")
    @classmethod
    def strip_label(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("字段名称不能为空")
        return value

    @model_validator(mode="after")
    def non_empty(self) -> FieldUpdate:
        if not self.model_fields_set:
            raise ValueError("至少需要提供一个修改字段")
        return self


class FieldRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    key: str
    label: str
    type: FieldType
    is_system: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime


class RecordRead(BaseModel):
    id: int
    values: dict[str, Any]
    sort_order: int
    created_at: datetime
    updated_at: datetime


class Summary(BaseModel):
    account_count: int
    total_followers: int
    total_notes: int
    field_count: int
    updated_at: datetime


class PageData(BaseModel):
    fields: list[FieldRead]
    records: list[RecordRead]
    summary: Summary


class RecordMutation(BaseModel):
    record: RecordRead
    summary: Summary


class RecordDelete(BaseModel):
    deleted_id: int
    summary: Summary


class FieldMutation(BaseModel):
    field: FieldRead
    default_value: str | int | None = None


class FieldDelete(BaseModel):
    deleted_id: int
    deleted_key: str
    summary: Summary


T = TypeVar("T")


class AccountDataResponse(BaseModel, Generic[T]):
    code: int = 0
    message: str = "success"
    data: T
