from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.models.bot_user import BotUser, UserRole
from bot.services.user_service import UserService
from bot.keyboards.user_mgmt_kb import build_user_list, build_user_actions
from bot.strings import (
    YOU_WERE_PROMOTED, YOU_WERE_PROMOTED_SUPERADMIN, YOU_WERE_DEMOTED, YOU_WERE_REMOVED,
    CANNOT_DEMOTE_OWNER, ADMIN_PROMOTED_USER, ADMIN_PROMOTED_SUPERADMIN
)

router = Router()

@router.message(Command("users"))
async def cmd_users(message: Message, bot_user: BotUser, session: AsyncSession):
    if bot_user.role not in [UserRole.SUPERADMIN, UserRole.ADMIN]:
        return

    users, total = await UserService.get_page(session, 1, 10)
    kb = build_user_list(users, 1, (total + 9) // 10)
    await message.answer("User Management", reply_markup=kb)

@router.callback_query(F.data.startswith("usr_p:"))
async def on_user_page(query: CallbackQuery, bot_user: BotUser, session: AsyncSession):
    if bot_user.role not in [UserRole.SUPERADMIN, UserRole.ADMIN]:
        return

    page = int(query.data.split(":")[1])
    users, total = await UserService.get_page(session, page, 10)
    kb = build_user_list(users, page, (total + 9) // 10)
    await query.message.edit_reply_markup(reply_markup=kb)
    await query.answer()

@router.callback_query(F.data.startswith("usr_a:"))
async def on_user_action(query: CallbackQuery, bot_user: BotUser, session: AsyncSession):
    parts = query.data.split(":")
    target_id = int(parts[1])
    action = parts[2]

    if action == "view":
        target = await UserService.get_by_id(session, target_id)
        if target:
            target_is_owner = (target.id == settings.bot.owner_id)
            kb = build_user_actions(target_id, target.role, bot_user.role, target_is_owner)
            await query.message.edit_text(
                f"User Info\n\nName: {target.full_name}\nRole: {target.role.value}\nJoined: {target.joined_at}",
                reply_markup=kb
            )
        await query.answer()
    elif action == "promote":
        if bot_user.role not in [UserRole.SUPERADMIN, UserRole.ADMIN]:
            await query.answer("Unauthorized", show_alert=True)
            return
        await UserService.promote(session, target_id, bot_user.id)
        await query.answer(f"User {target_id} promoted to Admin.")
    elif action == "promote_super":
        if bot_user.role != UserRole.SUPERADMIN:
            await query.answer("Unauthorized", show_alert=True)
            return
        await UserService.promote_to_superadmin(session, target_id, bot_user.id)
        await query.answer(f"User {target_id} promoted to Super Admin.")
    elif action == "demote":
        if bot_user.role != UserRole.SUPERADMIN:
            await query.answer("Unauthorized", show_alert=True)
            return
        if target_id == settings.bot.owner_id:
            await query.answer(CANNOT_DEMOTE_OWNER, show_alert=True)
            return
        await UserService.demote(session, target_id)
        await query.answer(f"User {target_id} demoted to User.")
    elif action == "demote_admin":
        if bot_user.role != UserRole.SUPERADMIN:
            await query.answer("Unauthorized", show_alert=True)
            return
        if target_id == settings.bot.owner_id:
            await query.answer(CANNOT_DEMOTE_OWNER, show_alert=True)
            return
        await UserService.demote_to_admin(session, target_id)
        await query.answer(f"User {target_id} demoted to Admin.")
    elif action == "remove":
        if bot_user.role not in [UserRole.SUPERADMIN, UserRole.ADMIN]:
            await query.answer("Unauthorized", show_alert=True)
            return
        if target_id == settings.bot.owner_id:
            await query.answer(CANNOT_DEMOTE_OWNER, show_alert=True)
            return
        await UserService.deactivate(session, target_id)
        await query.answer(f"User {target_id} deactivated.")
    else:
        await query.answer()
