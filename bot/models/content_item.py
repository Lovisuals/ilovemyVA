"bot/models/content_item.py"

import enum
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from sqlalchemy import String, Text, Boolean, Float, BigInteger, DateTime, Enum, Index, UUID
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base

class ContentBucket(enum.Enum):
    """
    Buckets for content organization.
    """
    DRAFTS = "drafts"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    ARCHIVE = "archive"

class ParseMode(enum.Enum):
    """
    Telegram message parse modes.
    """
    HTML = "HTML"
    MARKDOWN_V2 = "MarkdownV2"

class ContentItem(Base):
    """
    Represents a post or message created by an admin.
    """
    __tablename__ = "content_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bucket: Mapped[ContentBucket] = mapped_column(Enum(ContentBucket), nullable=False, index=True)
    text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    parse_mode: Mapped[ParseMode] = mapped_column(Enum(ParseMode), default=ParseMode.HTML)
    file_ids: Mapped[List[Dict[str, Any]]] = mapped_column(JSONB, default=list)
    media_group_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    has_poll: Mapped[bool] = mapped_column(Boolean, default=False)
    poll_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    recurrence: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    tz_name: Mapped[str] = mapped_column(String(64), default="Africa/Lagos")
    scheduler_job_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    tone_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    tone_flags: Mapped[List[str]] = mapped_column(JSONB, default=list)
    disclaimer_appended: Mapped[bool] = mapped_column(Boolean, default=False)
    content_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    created_by: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    archived_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    tags: Mapped[List[str]] = mapped_column(JSONB, default=list)
    metadata: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)

    __table_args__ = (
        Index("ix_content_items_bucket_scheduled_at", "bucket", "scheduled_at"),
        Index("ix_content_items_created_by_created_at", "created_by", "created_at"),
    )
