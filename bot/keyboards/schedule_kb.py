"bot/keyboards/schedule_kb.py"

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.callbacks import ScheduleTime, ScheduleCustom, ScheduleRecurrence

def build_time_picker(item_id: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    times = ["08:00", "10:00", "12:00", "16:00", "18:00", "22:00"]
    for t in times:
        builder.button(text=t, callback_data=ScheduleTime(item_id=item_id, time_str=t).pack())

    builder.button(text="⌨️ Custom Time", callback_data=ScheduleCustom(item_id=item_id).pack())

    builder.adjust(3, 3, 1)
    return builder.as_markup()

def build_recurrence_picker(item_id: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    options = [
        ("Once", "one_time"),
        ("Daily", "daily"),
        ("Weekly", "weekly"),
        ("Weekdays", "weekdays")
    ]

    for label, val in options:
        builder.button(text=label, callback_data=ScheduleRecurrence(item_id=item_id, recurrence=val).pack())

    builder.adjust(2, 2)
    return builder.as_markup()
