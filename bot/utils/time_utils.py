from datetime import datetime, timezone
import pytz
def get_now_tz(tz_name: str = "Africa/Lagos") -> datetime:
    tz = pytz.timezone(tz_name)
    return datetime.now(tz)
def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M") -> str:
    if not dt:
        return "N/A"
    return dt.strftime(format_str)
def get_countdown(dt: datetime) -> str:
    if not dt:
        return "N/A"
    now = datetime.now(timezone.utc)
    diff = dt - now
    if diff.total_seconds() < 0:
        return "Expired"
    days = diff.days
    hours, remainder = divmod(diff.seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    return " ".join(parts) or "<1m"
