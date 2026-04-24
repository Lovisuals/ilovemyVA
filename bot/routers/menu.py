from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.callbacks import NavData
from bot.keyboards.bucket_kb import build_bucket_list, build_bucket_panel
from bot.keyboards.menu_kb import build_main_menu, build_menu_row
from bot.keyboards.user_mgmt_kb import build_user_list
from bot.models.bot_user import BotUser, UserRole
from bot.models.content_item import ContentBucket, ContentItem
from bot.services.bucket_service import BucketService
from bot.services.persona_service import PersonaService
from bot.services.user_service import UserService
from bot.states.draft_states import DraftCreation
from bot.strings import (
    ADMIN_PANEL_HEADER, DRAFT_PROMPT, HELP_TEXT,
    MENU_ADMIN, MENU_PENDING, MENU_USER, SETTINGS_TEXT, STATS_TEXT,
)

router = Router()

_MENU_TEXT = {
    UserRole.SUPERADMIN: MENU_ADMIN,
    UserRole.ADMIN: MENU_ADMIN,
    UserRole.USER: MENU_USER,
    UserRole.PENDING: MENU_PENDING,
}


async def _show_menu(target, bot_user: BotUser, state: FSMContext = None):
    if state:
        await state.clear()
    text = _MENU_TEXT.get(bot_user.role, MENU_PENDING)
    kb = build_main_menu(bot_user.role)
    if isinstance(target, Message):
        await target.answer(text, reply_markup=kb)
    else:
        try:
            await target.message.edit_text(text, reply_markup=kb)
        except TelegramBadRequest:
            pass
        await target.answer()


@router.message(Command("menu"))
async def cmd_menu(message: Message, bot_user: BotUser):
    await _show_menu(message, bot_user)


@router.callback_query(NavData.filter(F.section == "menu"))
async def nav_menu(query: CallbackQuery, bot_user: BotUser, state: FSMContext):
    await _show_menu(query, bot_user, state)


@router.callback_query(NavData.filter(F.section == "new"))
async def nav_new(query: CallbackQuery, bot_user: BotUser, state: FSMContext):
    if bot_user.role not in (UserRole.ADMIN, UserRole.SUPERADMIN):
        await query.answer()
        return
    await state.set_state(DraftCreation.WAITING_CONTENT)
    builder = InlineKeyboardBuilder()
    builder.button(text="← Cancel", callback_data=NavData(section="menu").pack())
    await query.message.edit_text(DRAFT_PROMPT, reply_markup=builder.as_markup())
    await query.answer()


@router.callback_query(NavData.filter(F.section == "content"))
async def nav_content(query: CallbackQuery, bot_user: BotUser):
    if bot_user.role not in (UserRole.ADMIN, UserRole.SUPERADMIN):
        await query.answer()
        return
    await query.message.edit_text("📂 Content Library\n\nSelect a bucket:", reply_markup=build_bucket_list())
    await query.answer()


@router.callback_query(NavData.filter(F.section == "users"))
async def nav_users(query: CallbackQuery, bot_user: BotUser, session: AsyncSession):
    if bot_user.role not in (UserRole.ADMIN, UserRole.SUPERADMIN):
        await query.answer()
        return
    users, total = await UserService.get_page(session, 1, 10)
    kb = build_user_list(users, 1, (total + 9) // 10)
    await query.message.edit_text("👥 Team Management", reply_markup=kb)
    await query.answer()


@router.callback_query(NavData.filter(F.section == "settings"))
async def nav_settings(query: CallbackQuery, bot_user: BotUser):
    if bot_user.role not in (UserRole.ADMIN, UserRole.SUPERADMIN):
        await query.answer()
        return
    await query.message.edit_text(SETTINGS_TEXT, reply_markup=build_menu_row())
    await query.answer()


@router.callback_query(NavData.filter(F.section == "admin"))
async def nav_admin(query: CallbackQuery, bot_user: BotUser, session: AsyncSession):
    if bot_user.role not in (UserRole.ADMIN, UserRole.SUPERADMIN):
        await query.answer()
        return
    bucket = ContentBucket.DRAFTS
    items, total = await BucketService.get_page(session, bucket, 1, 10)
    total_pages = (total + 9) // 10
    kb = build_bucket_panel(bucket.value, items, 1, max(1, total_pages))
    await query.message.edit_text(
        ADMIN_PANEL_HEADER.format(bucket=bucket.value.capitalize()), reply_markup=kb
    )
    await query.answer()


@router.callback_query(NavData.filter(F.section == "stats"))
async def nav_stats(query: CallbackQuery, bot_user: BotUser, session: AsyncSession):
    if bot_user.role not in (UserRole.ADMIN, UserRole.SUPERADMIN):
        await query.answer()
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
    await query.message.edit_text(text, reply_markup=build_menu_row())
    await query.answer()


@router.callback_query(NavData.filter(F.section == "help"))
async def nav_help(query: CallbackQuery):
    await query.message.edit_text(HELP_TEXT, reply_markup=build_menu_row())
    await query.answer()
