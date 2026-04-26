from typing import List

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.callbacks import OnboardGen, UserAction, UserPage
from bot.keyboards.menu_kb import MENU_BTN
from bot.keyboards.pagination_kb import build_paginator_buttons
from bot.models.bot_user import BotUser, UserRole

_ROLE_ICON = {
    UserRole.SUPERADMIN: "👑",
    UserRole.ADMIN: "🛡",
    UserRole.USER: "👤",
    UserRole.PENDING: "🕒",
}

def build_user_list(users: List[BotUser], page: int, total_pages: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for user in users:
        icon = _ROLE_ICON.get(user.role, "❓")
        name = user.full_name or "Unknown"
        builder.row(
            InlineKeyboardButton(
                text=f"{icon} {name} (@{user.username or 'N/A'})",
                callback_data=UserAction(user_id=user.id, action="view").pack(),
            )
        )
    if total_pages > 1:
        paginator = build_paginator_buttons(UserPage, {}, page, total_pages)
        builder.row(*paginator)
    builder.row(MENU_BTN)
    return builder.as_markup()

def build_user_actions(user_id: int, current_role: UserRole) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if current_role == UserRole.PENDING:
        builder.button(text="🔑 Generate Code", callback_data=OnboardGen(user_id=user_id).pack())
    elif current_role == UserRole.USER:
        builder.button(text="🛡 Promote", callback_data=UserAction(user_id=user_id, action="promote").pack())
    elif current_role == UserRole.ADMIN:
        builder.button(text="👤 Demote", callback_data=UserAction(user_id=user_id, action="demote").pack())
    builder.button(text="🚫 Remove", callback_data=UserAction(user_id=user_id, action="remove").pack())
    builder.adjust(2)
    builder.row(
        InlineKeyboardButton(text="← Back to List", callback_data=UserPage(page=1).pack()),
        MENU_BTN,
    )
    return builder.as_markup()
