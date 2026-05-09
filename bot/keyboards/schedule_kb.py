from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.callbacks import ScheduleTime, ScheduleRecurrence
def build_time_picker(item_id: str, selected_times: list[str] = None) -> InlineKeyboardMarkup:
    if selected_times is None:
        selected_times = []
    builder = InlineKeyboardBuilder()
    for hour in range(24):
        for minute in [0, 30]:
            time_str = f"{hour:02d}{minute:02d}"
            display_str = f"{hour:02d}:{minute:02d}"
            text = f"[x] {display_str}" if time_str in selected_times else display_str
            builder.button(text=text, callback_data=ScheduleTime(item_id=item_id, time_str=time_str).pack())
    builder.adjust(6)
    from aiogram.types import InlineKeyboardButton
    builder.row(
        InlineKeyboardButton(
            text="Confirm Selection" if selected_times else "Confirm (All Day)",
            callback_data=ScheduleRecurrence(item_id=item_id, days="all").pack()
        )
    )
    return builder.as_markup()
def build_recurrence_picker(item_id: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    options = [("Once", "once"), ("Daily", "daily"), ("Weekly", "weekly")]
    for text, val in options:
        builder.button(text=text, callback_data=ScheduleRecurrence(item_id=item_id, recurrence=val).pack())
    builder.adjust(1)
    return builder.as_markup()
