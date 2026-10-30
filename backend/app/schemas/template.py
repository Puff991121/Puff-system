from __future__ import annotations

import re
from datetime import datetime
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit
from zoneinfo import ZoneInfo

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationInfo,
    computed_field,
    field_serializer,
    field_validator,
    model_validator,
)

TEMPLATE_FORMAT_FIELDS = {
    "Figma": "figma_share",
    "Psd": "psd_share",
    "Xd": "xd_share",
    "Jsd": "jsd_share",
    "Html": "html_share",
    "素材": "material_share",
}
SHARE_LABELS = {
    "figma_share": "Figma",
    "psd_share": "Psd",
    "xd_share": "Xd",
    "jsd_share": "Jsd（即时设计）",
    "html_share": "Html（源代码）",
    "material_share": "素材",
}
URL_PATTERN = re.compile(r"https?://[^\s<>\"'，。；、！？（）【】《》]+", re.IGNORECASE)
CODE_PATTERN = re.compile(r"提取码\s*[:：]?\s*([a-zA-Z0-9]{4})(?![a-zA-Z0-9])")
SHANGHAI = ZoneInfo("Asia/Shanghai")


def extract_share_url(content: str | None) -> str | None:
    """Extract a Baidu share URL while retaining the original text for copying."""
    if not content:
        return None
    for match in URL_PATTERN.finditer(content):
        candidate = match.group().rstrip(".,;:!?)]}")
        try:
            parts = urlsplit(candidate)
            if (
                parts.hostname != "pan.baidu.com"
                or parts.username is not None
                or parts.password is not None
                or parts.port not in (None, 80, 443)
            ):
                continue
            query = parse_qs(parts.query)
            short_share = re.fullmatch(r"/s/[a-zA-Z0-9_-]+/?", parts.path)
            legacy_share = (parts.path == "/share/init" and query.get("surl")) or (
                parts.path == "/share/link" and query.get("shareid") and query.get("uk")
            )
            if not short_share and not legacy_share:
                continue
            code = CODE_PATTERN.search(content)
            if not query.get("pwd") and code:
                # Replace an empty pwd parameter instead of adding a second one.
                from_query = [(key, value) for key, values in query.items() for value in values]
                from_query.append(("pwd", code.group(1)))
                return urlunsplit(parts._replace(query=urlencode(from_query)))
            return candidate
        except ValueError:
            continue
    return None


class TemplateShareFields(BaseModel):
    model_config = ConfigDict(extra="forbid")

    notes: str | None = Field(None, max_length=1000)
    figma_share: str | None = Field(None, max_length=2000)
    psd_share: str | None = Field(None, max_length=2000)
    xd_share: str | None = Field(None, max_length=2000)
    jsd_share: str | None = Field(None, max_length=2000)
    html_share: str | None = Field(None, max_length=2000)
    material_share: str | None = Field(None, max_length=2000)

    @field_validator("notes", *SHARE_LABELS)
    @classmethod
    def normalize_content(cls, value: str | None, info: ValidationInfo) -> str | None:
        value = value.strip() if value else None
        if value and info.field_name in SHARE_LABELS and extract_share_url(value) is None:
            raise ValueError(f"{SHARE_LABELS[info.field_name]} 需要包含有效的百度网盘分享链接")
        return value or None


class TemplateCreate(TemplateShareFields):
    name: str = Field(min_length=1, max_length=100)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("模板名称不能为空")
        return value

    @model_validator(mode="after")
    def require_share(self) -> TemplateCreate:
        if not any(getattr(self, field) for field in SHARE_LABELS):
            raise ValueError("请至少填写一项分享内容")
        return self


class TemplateUpdate(TemplateShareFields):
    name: str | None = Field(None, min_length=1, max_length=100)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str | None) -> str:
        if value is None or not value.strip():
            raise ValueError("模板名称不能为空")
        return value.strip()

    @model_validator(mode="after")
    def require_changes(self) -> TemplateUpdate:
        if not self.model_fields_set:
            raise ValueError("至少需要提供一个修改字段")
        return self


class TemplateRead(TemplateCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def share_urls(self) -> dict[str, str | None]:
        return {
            format_name: extract_share_url(getattr(self, field))
            for format_name, field in TEMPLATE_FORMAT_FIELDS.items()
        }

    @field_serializer("created_at", "updated_at")
    def serialize_datetime(self, value: datetime) -> str:
        if value.tzinfo is None:
            value = value.replace(tzinfo=SHANGHAI)
        return value.isoformat()


class TemplatePage(BaseModel):
    items: list[TemplateRead]
    total: int
    page: int
    page_size: int
    total_pages: int


class DeletedTemplate(BaseModel):
    deleted_id: int
