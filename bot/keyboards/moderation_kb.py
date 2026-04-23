from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.callbacks import ModerationResolve

def build_moderation_actions(event_id: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Approve", callback_data=ModerationResolve(event_id=event_id, resolution="APPROVED").pack())
    builder.button(text="⚠️ Warn", callback_data=ModerationResolve(event_id=event_id, resolution="WARN_ISSUED").pack())
    builder.button(text="🗑 Ignore", callback_data=ModerationResolve(event_id=event_id, resolution="IGNORED").pack())
    builder.adjust(2, 1)
    return builder.as_markup()
