from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.callbacks import ScheduleTime, ScheduleRecurrence

def build_time_picker(item_id: str, selected_times: list[str] = None) -> InlineKeyboardMarkup:
    if selected_times is None:
        selected_times = []
    
    builder = InlineKeyboardBuilder()
    for hour in range(24):
        h = hour % 12
        if h == 0:
            h = 12
        ampm = "AM" if hour < 12 else "PM"
        time_str = f"{hour:02d}:00"
        display_str = f"{h:02d}:00 {ampm}"
        
        text = f"✅ {display_str}" if time_str in selected_times else display_str
        builder.button(text=text, callback_data=ScheduleTime(item_id=item_id, time_str=time_str).pack())
    
    builder.adjust(4)
    
    count = len(selected_times)
    confirm_text = f"✅ Confirm ({count})" if count else "✅ Confirm"
    builder.row(InlineKeyboardButton(text=confirm_text, callback_data=ScheduleTime(item_id=item_id, time_str="confirm").pack()))
    
    return builder.as_markup()

def build_recurrence_picker(item_id: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    options = [("Once", "once"), ("Daily", "daily"), ("Weekly", "weekly")]
    for text, val in options:
        builder.button(text=text, callback_data=ScheduleRecurrence(item_id=item_id, recurrence=val).pack())
    builder.adjust(1)
    return builder.as_markup()
