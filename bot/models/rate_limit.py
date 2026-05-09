from datetime import datetime
from sqlalchemy import BigInteger, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column
from database.base import Base
class RateLimitEvent(Base):
    """
    Tracks request volume per user for database-backed rate limiting.
    """
    __tablename__ = "rate_limit_events"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    count: Mapped[int] = mapped_column(Integer, default=1)
