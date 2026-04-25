from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.callbacks import SettingsAction, NavData

def build_settings_panel(ai_enabled: bool, welcome_enabled: bool, timezone: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    ai_status = "🛡 Active" if ai_enabled else "⏸ Paused"
    welcome_status = "👋 Ready" if welcome_enabled else "⏸ Off"
    
    builder.button(text=f"Security Shield: {ai_status}",    callback_data=SettingsAction(action="toggle_ai").pack())
    builder.button(text=f"Welcome Protocol: {welcome_status}", callback_data=SettingsAction(action="toggle_welcome").pack())
    builder.button(text=f"Temporal Sync: {timezone}",    callback_data=SettingsAction(action="set_tz").pack())
    builder.button(text="📡 Signal Pulse",                callback_data=SettingsAction(action="view_api").pack())
    
    builder.button(text="🏠 Exit Config", callback_data=NavData(section="menu").pack())
    
    builder.adjust(1)
    return builder.as_markup()
