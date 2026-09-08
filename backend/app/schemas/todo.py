from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

PeriodType = Literal["daily", "weekly", "monthly"]
Priority = Literal["low", "medium", "high"]
TodoStatus = Literal["pending", "completed"]


class TodoCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    description: str | None = Field(None, max_length=1000)
    period_type: PeriodType
    scheduled_date: date
    priority: Priority = "medium"
    status: TodoStatus = "pending"

    @field_validator("title")
    @classmethod
    def strip_title(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("待办标题不能为空")
        return value

    @field_validator("description")
    @classmethod
    def strip_description(cls, value: str | None) -> str | None:
        value = value.strip() if value else None
        return value or None


class TodoUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=120)
    description: str | None = Field(None, max_length=1000)
    period_type: PeriodType | None = None
    scheduled_date: date | None = None
    priority: Priority | None = None
    status: TodoStatus | None = None

    @field_validator("title", "description")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else None

    @model_validator(mode="after")
    def ensure_non_empty(self):
        if not self.model_fields_set:
            raise ValueError("至少需要提供一个修改字段")
        if "title" in self.model_fields_set and not self.title:
            raise ValueError("待办标题不能为空")
        return self


class TodoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    period_type: PeriodType
    scheduled_date: date
    priority: Priority
    status: TodoStatus
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class TodoPage(BaseModel):
    items: list[TodoRead]
    total: int
    page: int
    page_size: int
    total_pages: int


class TodoSummary(BaseModel):
    total: int
    pending: int
    completed: int
    overdue: int
    daily: int
    weekly: int
    monthly: int
    completion_rate: int


class DeletedTodo(BaseModel):
    deleted_id: int
