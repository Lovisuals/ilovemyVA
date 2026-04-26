from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import BigInteger, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from database.base import Base

class UserWarning(Base):
    __tablename__ = "user_warnings"

    chat_id:        Mapped[int]           = mapped_column(BigInteger, primary_key=True)
    user_id:        Mapped[int]           = mapped_column(BigInteger, primary_key=True)
    warn_count:     Mapped[int]           = mapped_column(Integer, default=0, nullable=False)
    last_reason:    Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    last_warned_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)