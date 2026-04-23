"bot/models/audit_log.py"

from datetime import datetime, timezone
from typing import Optional, Dict, Any

from sqlalchemy import BigInteger, String, DateTime, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base

class AuditLog(Base):
    """
    System-wide audit trail for critical events and admin actions.
    """
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    event_code: Mapped[str] = mapped_column(String(64), index=True)
    actor_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    target_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    detail: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    level: Mapped[str] = mapped_column(String(16), default="INFO")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    __table_args__ = (
        Index("ix_audit_logs_event_code_created_at", "event_code", "created_at"),
    )
