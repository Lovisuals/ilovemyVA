from typing import List
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.callbacks import OnboardGen, UserAction, UserPage
from bot.keyboards.menu_kb import MENU_BTN
from bot.keyboards.pagination_kb import build_paginator_buttons
from bot.models.bot_user import BotUser, UserRole
_ROLE_ICON = {
    UserRole.SUPERADMIN: "",
    UserRole.ADMIN: "",
    UserRole.USER: "",
    UserRole.PENDING: "",
}
def build_user_list(users: List[BotUser], page: int, total_pages: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for user in users:
        icon = _ROLE_ICON.get(user.role, "?")
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
def build_user_actions(
    user_id: int,
    current_role: UserRole,
    viewer_role: UserRole,
    target_is_owner: bool = False,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if current_role == UserRole.PENDING:
        builder.button(
            text="Generate Code",
            callback_data=OnboardGen(user_id=user_id).pack(),
        )
    elif current_role == UserRole.USER:
        builder.button(
            text="Promote to Admin",
            callback_data=UserAction(user_id=user_id, action="promote").pack(),
        )
    elif current_role == UserRole.ADMIN:
        if viewer_role == UserRole.SUPERADMIN:
            builder.button(
                text="Promote to Super Admin",
                callback_data=UserAction(user_id=user_id, action="promote_super").pack(),
            )
        builder.button(
            text="Demote to User",
            callback_data=UserAction(user_id=user_id, action="demote").pack(),
        )
    elif current_role == UserRole.SUPERADMIN:
        if viewer_role == UserRole.SUPERADMIN and not target_is_owner:
            builder.button(
                text="Demote to Admin",
                callback_data=UserAction(user_id=user_id, action="demote_admin").pack(),
            )
    if not target_is_owner:
        builder.button(
            text="Remove Access",
            callback_data=UserAction(user_id=user_id, action="remove").pack(),
        )
    builder.adjust(1)
    builder.row(
        InlineKeyboardButton(text="Back", callback_data=UserPage(page=1).pack()),
        MENU_BTN,
    )
    return builder.as_markup()
def build_superadmin_contact_kb(superadmins: List[BotUser]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for sa in superadmins:
        if sa.username:
            name = sa.full_name or sa.username
            builder.row(
                InlineKeyboardButton(
                    text=f"Message {name}",
                    url=f"https://t.me/{sa.username}",
                )
            )
    return builder.as_markup()
