import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import BigInteger, Boolean, DateTime, String, UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base


class BotPersona(Base):
    __tablename__ = "bot_personas"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    signature: Mapped[str] = mapped_column(String(256), default="— {name}")
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_by: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
