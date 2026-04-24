from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import BigInteger, Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column
from database.base import Base


class ConnectedChat(Base):
    __tablename__ = "connected_chats"

    chat_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    username: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    chat_type: Mapped[str] = mapped_column(String(16), nullable=False)   # group/supergroup/channel
    bot_status: Mapped[str] = mapped_column(String(16), nullable=False)  # member/administrator/left/kicked
    is_broadcast_target: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    last_active_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
