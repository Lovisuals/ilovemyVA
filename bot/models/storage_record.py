import enum
import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import BigInteger, String, Enum, DateTime, ForeignKey, UUID
from sqlalchemy.orm import Mapped, mapped_column
from database.base import Base
class FileType(enum.Enum):
    """
    Types of files stored in the Telegram storage channel.
    """
    PHOTO = "photo"
    VIDEO = "video"
    DOCUMENT = "document"
    AUDIO = "audio"
    VOICE = "voice"
    ANIMATION = "animation"
class StorageRecord(Base):
    """
    Metadata for files archived in the Telegram storage channel.
    """
    __tablename__ = "storage_records"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    original_filename: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    file_id: Mapped[str] = mapped_column(String(256))
    file_unique_id: Mapped[str] = mapped_column(String(128), unique=True)
    file_type: Mapped[FileType] = mapped_column(Enum(FileType))
    file_size: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    storage_message_id: Mapped[int] = mapped_column(BigInteger)
    storage_channel_id: Mapped[int] = mapped_column(BigInteger)
    uploaded_by: Mapped[int] = mapped_column(BigInteger)
    content_item_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("content_items.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
