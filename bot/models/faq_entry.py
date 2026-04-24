import uuid
from datetime import datetime, timezone

from sqlalchemy import BigInteger, Boolean, DateTime, String, Text, UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base


class FaqEntry(Base):
    __tablename__ = "faq_entries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trigger: Mapped[str] = mapped_column(String(256), nullable=False)
    response: Mapped[str] = mapped_column(Text, nullable=False)
    match_type: Mapped[str] = mapped_column(String(16), default="contains")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_by: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
