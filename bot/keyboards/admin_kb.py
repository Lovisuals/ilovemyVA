from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.callbacks import ControlAction, NavData

def build_admin_dashboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    builder.button(text="System Health", callback_data=ControlAction(action="health").pack())
    builder.button(text="Audit Logs",   callback_data=ControlAction(action="audit").pack())
    builder.button(text="Sync Network",  callback_data=ControlAction(action="sync").pack())
    builder.button(text="Flush Queue",   callback_data=ControlAction(action="flush").pack())
    builder.button(text="Broadcast Hub", callback_data=ControlAction(action="broadcast").pack())
    
    builder.button(text="Exit Dashboard", callback_data=NavData(section="menu").pack())
    
    builder.adjust(2, 2, 1, 1)
    return builder.as_markup()
