from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.callbacks import SettingsAction, NavData

def build_settings_panel(ai_enabled: bool, welcome_enabled: bool, timezone: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    ai_status = "✅" if ai_enabled else "❌"
    welcome_status = "✅" if welcome_enabled else "❌"
    
    builder.button(text=f"🤖 AI Review: {ai_status}",    callback_data=SettingsAction(action="toggle_ai").pack())
    builder.button(text=f"👋 Welcome Msg: {welcome_status}", callback_data=SettingsAction(action="toggle_welcome").pack())
    builder.button(text=f"🕒 Timezone: {timezone}",    callback_data=SettingsAction(action="set_tz").pack())
    builder.button(text="🔌 API Status",                callback_data=SettingsAction(action="view_api").pack())
    
    builder.button(text="🏠 Main Menu", callback_data=NavData(section="menu").pack())
    
    builder.adjust(2, 1, 1, 1)
    return builder.as_markup()
