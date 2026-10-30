from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationInfo,
    field_serializer,
    field_validator,
    model_validator,
)

SHANGHAI = ZoneInfo("Asia/Shanghai")


class XianyuLinkCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=200)
    link: str = Field(min_length=1, max_length=2000)

    @field_validator("title", "link", mode="before")
    @classmethod
    def normalize_text(cls, value: str, info: ValidationInfo) -> str:
        label = "闲鱼标题" if info.field_name == "title" else "闲鱼链接"
        if value is None or (isinstance(value, str) and not value.strip()):
            raise ValueError(f"{label}不能为空")
        return value.strip() if isinstance(value, str) else value


class XianyuLinkUpdate(XianyuLinkCreate):
    title: str | None = Field(None, min_length=1, max_length=200)
    link: str | None = Field(None, min_length=1, max_length=2000)

    @model_validator(mode="after")
    def require_changes(self) -> XianyuLinkUpdate:
        if not self.model_fields_set:
            raise ValueError("至少需要提供一个修改字段")
        return self


class XianyuLinkRead(XianyuLinkCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime

    @field_serializer("created_at", "updated_at")
    def serialize_datetime(self, value: datetime) -> str:
        if value.tzinfo is None:
            value = value.replace(tzinfo=SHANGHAI)
        return value.isoformat()


class XianyuLinkPage(BaseModel):
    items: list[XianyuLinkRead]
    total: int
    page: int
    page_size: int
    total_pages: int


class DeletedXianyuLink(BaseModel):
    deleted_id: int
