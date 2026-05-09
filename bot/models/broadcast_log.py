import enum
import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import BigInteger, String, Enum, DateTime, ForeignKey, UUID
from sqlalchemy.orm import Mapped, mapped_column
from database.base import Base
class BroadcastStatus(enum.Enum):
    """
    Status of a broadcast delivery attempt.
    """
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    SKIPPED_DEDUP = "skipped_dedup"
class BroadcastLog(Base):
    """
    Records the delivery of content to specific targets.
    """
    __tablename__ = "broadcast_logs"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("content_items.id", ondelete="CASCADE"), index=True)
    target_chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    target_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    message_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    status: Mapped[BroadcastStatus] = mapped_column(Enum(BroadcastStatus))
    error_detail: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
