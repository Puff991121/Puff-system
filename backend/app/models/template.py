from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Template(Base):
    __tablename__ = "templates"
    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uk_templates_user_name"),
        Index("idx_templates_user_updated", "user_id", "updated_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text(), nullable=True)
    figma_share: Mapped[Optional[str]] = mapped_column(Text(), nullable=True)
    psd_share: Mapped[Optional[str]] = mapped_column(Text(), nullable=True)
    xd_share: Mapped[Optional[str]] = mapped_column(Text(), nullable=True)
    material_share: Mapped[Optional[str]] = mapped_column(Text(), nullable=True)
    jsd_share: Mapped[Optional[str]] = mapped_column(Text(), nullable=True)
    html_share: Mapped[Optional[str]] = mapped_column(Text(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
