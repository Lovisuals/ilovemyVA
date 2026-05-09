from typing import Optional
from bot.config import settings

def get_editor_url() -> Optional[str]:
    if settings.bot.webhook_url:
        return f"{settings.bot.webhook_url}/static/editor.html"
    return None
