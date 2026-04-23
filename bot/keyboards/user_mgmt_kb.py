"bot/keyboards/user_mgmt_kb.py"

from typing import List
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.callbacks import UserAction, UserPage
from bot.models.bot_user import BotUser, UserRole
from bot.keyboards.pagination_kb import build_paginator_buttons

def build_user_list(users: List[BotUser], page: int, total_pages: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    role_icons = {
        UserRole.SUPERADMIN: "👑",
        UserRole.ADMIN: "🛡",
        UserRole.USER: "👤",
        UserRole.PENDING: "🕒"
    }

    for user in users:
        icon = role_icons.get(user.role, "❓")
        name = user.full_name or "Unknown"
        builder.row(
            builder.button(
                text=f"{icon} {name} (@{user.username or 'N/A'})",
                callback_data=UserAction(user_id=user.id, action="view").pack()
            ).button
        )

    if total_pages > 1:
        paginator = build_paginator_buttons(UserPage, {}, page, total_pages)
        builder.row(*paginator)

    return builder.as_markup()

def build_user_actions(user_id: int, current_role: UserRole) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    if current_role == UserRole.USER:
        builder.button(text="🛡 Promote", callback_data=UserAction(user_id=user_id, action="promote").pack())
    elif current_role == UserRole.ADMIN:
        builder.button(text="👤 Demote", callback_data=UserAction(user_id=user_id, action="demote").pack())

    builder.button(text="🚫 Remove", callback_data=UserAction(user_id=user_id, action="remove").pack())
    builder.button(text="← Back", callback_data=UserPage(page=1).pack())

    builder.adjust(2, 1)
    return builder.as_markup()
