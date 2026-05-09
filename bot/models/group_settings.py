from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import BigInteger, Boolean, DateTime, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column
from database.base import Base
class GroupSettings(Base):
    __tablename__ = "group_settings"
    chat_id:      Mapped[int]           = mapped_column(BigInteger, primary_key=True)
    mod_enabled:  Mapped[bool]          = mapped_column(Boolean, default=False, nullable=False)
    link_filter:  Mapped[bool]          = mapped_column(Boolean, default=False, nullable=False)
    warn_limit:   Mapped[int]           = mapped_column(Integer,  default=3,     nullable=False)
    keyword_list: Mapped[Optional[str]] = mapped_column(Text,    nullable=True)
    updated_at:   Mapped[datetime]      = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
