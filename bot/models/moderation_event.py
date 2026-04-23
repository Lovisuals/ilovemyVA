"bot/models/moderation_event.py"

import enum
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from sqlalchemy import BigInteger, String, Enum, DateTime, UUID
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base

class ModerationEventType(enum.Enum):
    """
    Types of moderation events detected or manually triggered.
    """
    SPAM = "spam"
    TONE_FLAG = "tone_flag"
    WARN = "warn"
    MUTE = "mute"
    BAN_REQUEST = "ban_request"
    DELETE = "delete"

class ModerationResolution(enum.Enum):
    """
    Resolution status of a moderation event by an admin.
    """
    APPROVED = "approved"
    IGNORED = "ignored"
    WARN_ISSUED = "warn_issued"

class ModerationEvent(Base):
    """
    Tracks moderation actions and AI-detected flags.
    """
    __tablename__ = "moderation_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type: Mapped[ModerationEventType] = mapped_column(Enum(ModerationEventType))
    actor_user_id: Mapped[int] = mapped_column(BigInteger)
    chat_id: Mapped[int] = mapped_column(BigInteger)
    message_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    resolved_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    resolution: Mapped[Optional[ModerationResolution]] = mapped_column(Enum(ModerationResolution), nullable=True)
    detail: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
