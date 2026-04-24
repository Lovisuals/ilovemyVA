from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.callbacks import ScheduleTime, ScheduleRecurrence

def build_time_picker(item_id: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for hour in range(0, 24, 2):
        time_str = f"{hour:02d}:00"
        builder.button(text=time_str, callback_data=ScheduleTime(item_id=item_id, time_str=time_str).pack())
    builder.adjust(4)
    return builder.as_markup()

def build_recurrence_picker(item_id: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    options = [("Once", "once"), ("Daily", "daily"), ("Weekly", "weekly")]
    for text, val in options:
        builder.button(text=text, callback_data=ScheduleRecurrence(item_id=item_id, recurrence=val).pack())
    builder.adjust(1)
    return builder.as_markup()
