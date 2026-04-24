from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.callbacks import NavData
from bot.models.bot_user import UserRole

MENU_BTN = InlineKeyboardButton(
    text="🏠 Menu",
    callback_data=NavData(section="menu").pack(),
)


def build_main_menu(role: UserRole) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if role in (UserRole.ADMIN, UserRole.SUPERADMIN):
        builder.button(text="✏️ New Draft",      callback_data=NavData(section="new").pack())
        builder.button(text="📂 Library",         callback_data=NavData(section="content").pack())
        builder.button(text="👥 Team",            callback_data=NavData(section="users").pack())
        builder.button(text="⚙️ Settings",        callback_data=NavData(section="settings").pack())
        builder.button(text="📊 Control Centre",  callback_data=NavData(section="admin").pack())
        builder.adjust(2, 2, 1)
    elif role == UserRole.USER:
        builder.button(text="❓ Help & Commands", callback_data=NavData(section="help").pack())
        builder.adjust(1)
    return builder.as_markup()


def build_menu_row() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(MENU_BTN)
    return builder.as_markup()
