"bot/keyboards/moderation_kb.py"

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.callbacks import ModerationResolve

def build_moderation_actions(event_id: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    builder.button(text="✅ Approve", callback_data=ModerationResolve(event_id=event_id, resolution="approved"))
    builder.button(text="⚠️ Warn", callback_data=ModerationResolve(event_id=event_id, resolution="warn_issued"))
    builder.button(text="⏭ Ignore", callback_data=ModerationResolve(event_id=event_id, resolution="ignored"))
    
    builder.adjust(3)
    return builder.as_markup()
