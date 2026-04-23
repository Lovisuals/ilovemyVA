from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

def build_time_picker(item_id: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for hour in range(0, 24, 2):
        time_str = f"{hour:02d}:00"
        builder.button(text=time_str, callback_data=f"sch_t:{item_id}:{time_str}")
    builder.adjust(4)
    return builder.as_markup()

def build_recurrence_picker(item_id: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    options = [("Once", "once"), ("Daily", "daily"), ("Weekly", "weekly")]
    for text, val in options:
        builder.button(text=text, callback_data=f"sch_r:{item_id}:{val}")
    builder.adjust(1)
    return builder.as_markup()
