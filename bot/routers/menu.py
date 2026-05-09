from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from bot.callbacks import NavData
from bot.keyboards.bucket_kb import build_bucket_list
from bot.keyboards.menu_kb import build_main_menu, build_menu_row
from bot.keyboards.user_mgmt_kb import build_user_list
from bot.models.bot_user import BotUser, UserRole
from bot.models.content_item import ContentBucket, ContentItem
from bot.services.persona_service import PersonaService
from bot.services.user_service import UserService
from bot.keyboards.admin_kb import build_admin_dashboard
from bot.keyboards.settings_kb import build_settings_panel
from bot.services.system_service import SystemService
from bot.strings import (
    HELP_TEXT, MENU_ADMIN, MENU_PENDING, MENU_USER, STATS_TEXT,
)
router = Router()
_MENU_TEXT = {
    UserRole.SUPERADMIN: MENU_ADMIN,
    UserRole.ADMIN: MENU_ADMIN,
    UserRole.USER: MENU_USER,
    UserRole.PENDING: MENU_PENDING,
}
async def _safe_edit(query: CallbackQuery, text: str, reply_markup=None):
    try:
        await query.message.edit_text(text, reply_markup=reply_markup)
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            return
        if "can't parse entities" in str(e):
            await query.message.edit_text(text, reply_markup=reply_markup, parse_mode=None)
        else:
            raise
async def _show_menu(target, bot_user: BotUser, state: FSMContext = None):
    if state:
        await state.clear()
    text = _MENU_TEXT.get(bot_user.role, MENU_PENDING)
    kb = build_main_menu(bot_user.role)
    if isinstance(target, Message):
        await target.answer(text, reply_markup=kb)
    else:
        await _safe_edit(target, text, reply_markup=kb)
@router.message(Command("menu"))
async def cmd_menu(message: Message, bot_user: BotUser):
    await _show_menu(message, bot_user)
@router.callback_query(NavData.filter(F.section == "menu"))
async def nav_menu(query: CallbackQuery, bot_user: BotUser, state: FSMContext):
    await query.answer()
    await _show_menu(query, bot_user, state)
@router.callback_query(NavData.filter(F.section == "content"))
async def nav_content(query: CallbackQuery, bot_user: BotUser):
    await query.answer()
    if bot_user.role not in (UserRole.ADMIN, UserRole.SUPERADMIN):
        return
    await _safe_edit(query, "Content Library\n\nSelect a bucket:", reply_markup=build_bucket_list())
@router.callback_query(NavData.filter(F.section == "users"))
async def nav_users(query: CallbackQuery, bot_user: BotUser, session: AsyncSession):
    await query.answer()
    if bot_user.role not in (UserRole.ADMIN, UserRole.SUPERADMIN):
        return
    users, total = await UserService.get_page(session, 1, 10)
    kb = build_user_list(users, 1, (total + 9) // 10)
    await _safe_edit(query, "Team Management", reply_markup=kb)
@router.callback_query(NavData.filter(F.section == "settings"))
async def nav_settings(query: CallbackQuery, bot_user: BotUser):
    await query.answer()
    if bot_user.role not in (UserRole.ADMIN, UserRole.SUPERADMIN):
        return
    kb = build_settings_panel(True, False, "Africa/Lagos")
    text = (
        "System Configuration\n"
        "─" * 28 + "\n"
        "Global parameters and operational toggles."
    )
    await _safe_edit(query, text, reply_markup=kb)
@router.callback_query(NavData.filter(F.section == "admin"))
async def nav_admin(query: CallbackQuery, bot_user: BotUser, session: AsyncSession):
    await query.answer()
    if bot_user.role not in (UserRole.ADMIN, UserRole.SUPERADMIN):
        return
    me = await query.bot.get_me()
    stats = await SystemService.get_dashboard_data(session, me.username)
    text = (
        "Command Centre\n"
        "─" * 28 + "\n"
        f"DB: {stats['db_status']} | BOT: @{stats['bot_username']}\n"
        f"VAULT: {stats['storage_vault']} ({stats['vault_status']})\n"
        "─" * 28 + "\n"
        f"QUEUED: {stats['scheduled']} | DRAFTS: {stats['drafts']}\n"
        f"TEAM: {stats['users']} | CHATS: {stats['chats']}\n\n"
        "Recent Activity:\n"
        f"{stats['audit_trail']}\n"
        f"Pulse: {stats['timestamp']}"
    )
    kb = build_admin_dashboard()
    await _safe_edit(query, text, reply_markup=kb)
@router.callback_query(NavData.filter(F.section == "stats"))
async def nav_stats(query: CallbackQuery, bot_user: BotUser, session: AsyncSession):
    await query.answer()
    if bot_user.role not in (UserRole.ADMIN, UserRole.SUPERADMIN):
        return
    counts: dict[str, int] = {}
    for bucket in ContentBucket:
        result = await session.execute(
            select(func.count()).select_from(ContentItem).where(ContentItem.bucket == bucket)
        )
        counts[bucket.value] = result.scalar() or 0
    _, total_users = await UserService.get_page(session, 1, 1)
    persona = await PersonaService.get_active(session)
    text = STATS_TEXT.format(
        drafts=counts.get("drafts", 0),
        scheduled=counts.get("scheduled", 0),
        published=counts.get("published", 0),
        archive=counts.get("archive", 0),
        users=total_users,
        persona=persona.name if persona else "None set",
    )
    await _safe_edit(query, text, reply_markup=build_menu_row())
@router.callback_query(NavData.filter(F.section == "help"))
async def nav_help(query: CallbackQuery):
    await query.answer()
    await _safe_edit(query, HELP_TEXT, reply_markup=build_menu_row())
