from typing import List

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.callbacks import FaqAction, NavData
from bot.keyboards.menu_kb import MENU_BTN
from bot.models.faq_entry import FaqEntry

def build_faq_list(entries: List[FaqEntry]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for e in entries:
        label = f"{'✅' if e.is_active else '○'} {e.trigger[:32]}{'…' if len(e.trigger) > 32 else ''}"
        builder.row(
            InlineKeyboardButton(
                text=label,
                callback_data=FaqAction(entry_id=str(e.id), action="view").pack(),
            )
        )
    builder.row(
        InlineKeyboardButton(text="➕ Add Reply", callback_data=NavData(section="faq_new").pack())
    )
    builder.row(MENU_BTN)
    return builder.as_markup()

def build_faq_actions(entry_id: str, is_active: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="⏸ Disable" if is_active else "▶️ Enable",
        callback_data=FaqAction(entry_id=entry_id, action="toggle").pack(),
    )
    builder.button(
        text="🗑 Delete",
        callback_data=FaqAction(entry_id=entry_id, action="delete").pack(),
    )
    builder.adjust(2)
    builder.row(
        InlineKeyboardButton(text="← Back", callback_data=NavData(section="faq").pack()),
        MENU_BTN,
    )
    return builder.as_markup()
