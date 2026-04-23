"bot/models/bot_user.py"

import enum
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import BigInteger, String, Enum, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base

class UserRole(enum.Enum):
    """
    User roles for access control.
    superadmin: System owner (OWNER_ID)
    admin: Promoted user with management rights
    user: Onboarded user with content access
    pending: New user awaiting verification
    """
    SUPERADMIN = "superadmin"
    ADMIN = "admin"
    USER = "user"
    PENDING = "pending"

class BotUser(Base):
    """
    Represents a Telegram user interacting with the bot.
    """
    __tablename__ = "bot_users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    full_name: Mapped[str] = mapped_column(String(256))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.PENDING)
    verification_code: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    code_generated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    code_used: Mapped[bool] = mapped_column(Boolean, default=False)
    promoted_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("bot_users.id"), nullable=True)
    invited_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("bot_users.id"), nullable=True)
    joined_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_seen: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
