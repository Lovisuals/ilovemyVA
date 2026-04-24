import json
import logging

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.callbacks import GroupChatConfig, NavData
from bot.keyboards.menu_kb import MENU_BTN, build_menu_row
from bot.models.bot_user import BotUser, UserRole
from bot.models.connected_chat import ConnectedChat
from bot.models.welcome_config import WelcomeConfig
from bot.services.group_settings_service import GroupSettingsService, WarnService
from bot.states.feature_states import GroupKwSetup, WelcomeSetup
from bot.strings import (
    GROUP_KW_ENTER, GROUP_KW_SAVED, GROUP_PANEL, GROUP_PANEL_EMPTY,
    GROUP_SETTINGS_LIST,
)

logger = logging.getLogger(__name__)
router = Router()


async def _require_admin(bot: Bot, chat_id: int, user_id: int) -> bool:
    try:
        m = await bot.get_chat_member(chat_id, user_id)
        return m.status in ("administrator", "creator")
    except Exception:
        return False


def _mention(user) -> str:
    return f"@{user.username}" if user.username else user.full_name


def _panel_kb(chat_id: int, gs, welcome_active: bool) -> any:
    builder = InlineKeyboardBuilder()
    mod_label  = "🛡 Mod: ON"  if gs.mod_enabled  else "🛡 Mod: OFF"
    link_label = "🔗 Links: Block" if gs.link_filter else "🔗 Links: Allow"
    builder.button(text=mod_label,   callback_data=GroupChatConfig(chat_id=chat_id, action="toggle_mod").pack())
    builder.button(text=link_label,  callback_data=GroupChatConfig(chat_id=chat_id, action="toggle_link").pack())
    builder.adjust(2)
    builder.button(
        text=f"⚠️ Warn limit: {gs.warn_limit}",
        callback_data=GroupChatConfig(chat_id=chat_id, action="cycle_warn").pack(),
    )
    builder.button(
        text="🚫 Edit banned words",
        callback_data=GroupChatConfig(chat_id=chat_id, action="edit_kw").pack(),
    )
    builder.adjust(2)
    w_label = "👋 Welcome: ON" if welcome_active else "👋 Welcome: OFF"
    builder.button(text=w_label,       callback_data=GroupChatConfig(chat_id=chat_id, action="toggle_welcome").pack())
    builder.button(text="✏️ Edit welcome", callback_data=GroupChatConfig(chat_id=chat_id, action="edit_welcome").pack())
    builder.adjust(2)
    builder.row(MENU_BTN)
    return builder.as_markup()


async def _show_panel(bot_or_query, chat_id: int, session: AsyncSession, edit: bool = False):
    if isinstance(bot_or_query, CallbackQuery):
        query   = bot_or_query
        send_fn = query.message.edit_text if edit else query.message.answer
    else:
        send_fn = bot_or_query.answer

    gs    = await GroupSettingsService.get_or_default(session, chat_id)
    wconf = await session.scalar(select(WelcomeConfig).where(WelcomeConfig.chat_id == chat_id))

    result = await session.execute(select(ConnectedChat).where(ConnectedChat.chat_id == chat_id))
    chat   = result.scalar_one_or_none()
    name   = chat.title if chat else str(chat_id)

    kw_count = len(json.loads(gs.keyword_list)) if gs.keyword_list else 0
    welcome_preview = (wconf.message[:80] + "…") if wconf and wconf.message else "Not set"
    text = GROUP_PANEL.format(
        name=name,
        mod="✅ ON" if gs.mod_enabled  else "⏸ OFF",
        links="🚫 Blocked" if gs.link_filter else "✅ Allowed",
        warn_limit=gs.warn_limit,
        kw_count=kw_count,
        welcome="✅ Active" if (wconf and wconf.is_active) else "⏸ Off",
        welcome_preview=welcome_preview,
    )
    kb = _panel_kb(chat_id, gs, bool(wconf and wconf.is_active))
    try:
        await send_fn(text, reply_markup=kb)
    except TelegramBadRequest:
        pass


@router.callback_query(NavData.filter(F.section == "groups"))
async def nav_groups(query: CallbackQuery, bot_user: BotUser, session: AsyncSession):
    if bot_user.role not in (UserRole.ADMIN, UserRole.SUPERADMIN):
        await query.answer()
        return
    result = await session.execute(
        select(ConnectedChat)
        .where(ConnectedChat.bot_status.in_({"member", "administrator"}))
        .order_by(ConnectedChat.title)
    )
    chats = result.scalars().all()
    if not chats:
        await query.message.edit_text(GROUP_PANEL_EMPTY, reply_markup=build_menu_row())
        await query.answer()
        return
    builder = InlineKeyboardBuilder()
    for c in chats:
        icon = "🔊" if c.chat_type == "channel" else "👥"
        builder.button(
            text=f"{icon} {c.title}",
            callback_data=GroupChatConfig(chat_id=c.chat_id, action="view").pack(),
        )
    builder.adjust(1)
    builder.row(MENU_BTN)
    await query.message.edit_text(GROUP_SETTINGS_LIST, reply_markup=builder.as_markup())
    await query.answer()


@router.callback_query(GroupChatConfig.filter(F.action == "view"))
async def group_view(query: CallbackQuery, callback_data: GroupChatConfig,
                     bot_user: BotUser, session: AsyncSession):
    if bot_user.role not in (UserRole.ADMIN, UserRole.SUPERADMIN):
        await query.answer(); return
    await _show_panel(query, callback_data.chat_id, session, edit=True)
    await query.answer()


@router.callback_query(GroupChatConfig.filter(F.action == "toggle_mod"))
async def toggle_mod(query: CallbackQuery, callback_data: GroupChatConfig,
                     bot_user: BotUser, session: AsyncSession):
    if bot_user.role not in (UserRole.ADMIN, UserRole.SUPERADMIN):
        await query.answer(); return
    gs = await GroupSettingsService.get_or_default(session, callback_data.chat_id)
    await GroupSettingsService.upsert(session, callback_data.chat_id, mod_enabled=not gs.mod_enabled)
    await _show_panel(query, callback_data.chat_id, session, edit=True)
    await query.answer()


@router.callback_query(GroupChatConfig.filter(F.action == "toggle_link"))
async def toggle_link(query: CallbackQuery, callback_data: GroupChatConfig,
                      bot_user: BotUser, session: AsyncSession):
    if bot_user.role not in (UserRole.ADMIN, UserRole.SUPERADMIN):
        await query.answer(); return
    gs = await GroupSettingsService.get_or_default(session, callback_data.chat_id)
    await GroupSettingsService.upsert(session, callback_data.chat_id, link_filter=not gs.link_filter)
    await _show_panel(query, callback_data.chat_id, session, edit=True)
    await query.answer()


@router.callback_query(GroupChatConfig.filter(F.action == "cycle_warn"))
async def cycle_warn(query: CallbackQuery, callback_data: GroupChatConfig,
                     bot_user: BotUser, session: AsyncSession):
    if bot_user.role not in (UserRole.ADMIN, UserRole.SUPERADMIN):
        await query.answer(); return
    gs    = await GroupSettingsService.get_or_default(session, callback_data.chat_id)
    new_limit = (gs.warn_limit % 5) + 1
    await GroupSettingsService.upsert(session, callback_data.chat_id, warn_limit=new_limit)
    await _show_panel(query, callback_data.chat_id, session, edit=True)
    await query.answer(f"Warn limit set to {new_limit}")


@router.callback_query(GroupChatConfig.filter(F.action == "edit_kw"))
async def edit_kw_start(query: CallbackQuery, callback_data: GroupChatConfig,
                        bot_user: BotUser, state: FSMContext):
    if bot_user.role not in (UserRole.ADMIN, UserRole.SUPERADMIN):
        await query.answer(); return
    await state.set_state(GroupKwSetup.ENTERING_KEYWORDS)
    await state.update_data(gk_chat_id=callback_data.chat_id)
    builder = InlineKeyboardBuilder()
    builder.button(text="← Back", callback_data=GroupChatConfig(chat_id=callback_data.chat_id, action="view").pack())
    await query.message.edit_text(GROUP_KW_ENTER, reply_markup=builder.as_markup())
    await query.answer()


@router.message(GroupKwSetup.ENTERING_KEYWORDS, F.chat.type == "private")
async def edit_kw_received(message: Message, state: FSMContext, session: AsyncSession):
    data     = await state.get_data()
    chat_id  = data["gk_chat_id"]
    raw      = message.text or ""
    keywords = [w.strip().lower() for w in raw.split(",") if w.strip()]
    kw_json  = json.dumps(keywords) if keywords else None
    await GroupSettingsService.upsert(session, chat_id, keyword_list=kw_json)
    await state.clear()
    await message.answer(GROUP_KW_SAVED.format(count=len(keywords)), reply_markup=build_menu_row())


@router.callback_query(GroupChatConfig.filter(F.action == "toggle_welcome"))
async def toggle_welcome(query: CallbackQuery, callback_data: GroupChatConfig,
                         bot_user: BotUser, session: AsyncSession):
    if bot_user.role not in (UserRole.ADMIN, UserRole.SUPERADMIN):
        await query.answer(); return
    wconf = await session.scalar(
        select(WelcomeConfig).where(WelcomeConfig.chat_id == callback_data.chat_id)
    )
    if wconf:
        wconf.is_active = not wconf.is_active
        await session.commit()
    await _show_panel(query, callback_data.chat_id, session, edit=True)
    await query.answer()


@router.callback_query(GroupChatConfig.filter(F.action == "edit_welcome"))
async def edit_welcome_start(query: CallbackQuery, callback_data: GroupChatConfig,
                              bot_user: BotUser, state: FSMContext):
    if bot_user.role not in (UserRole.ADMIN, UserRole.SUPERADMIN):
        await query.answer(); return
    await state.set_state(WelcomeSetup.ENTERING_MESSAGE)
    await state.update_data(welcome_chat_id=callback_data.chat_id)
    builder = InlineKeyboardBuilder()
    builder.button(text="← Back", callback_data=GroupChatConfig(chat_id=callback_data.chat_id, action="view").pack())
    await query.message.edit_text(
        "Send the welcome message for this group.\n\n"
        "Use {name}, {username}, {chat} as placeholders.",
        reply_markup=builder.as_markup(),
    )
    await query.answer()


@router.message(Command("warn"), F.chat.type.in_({"group", "supergroup"}))
async def cmd_warn(message: Message, bot: Bot, session: AsyncSession):
    if not await _require_admin(bot, message.chat.id, message.from_user.id):
        return
    target = message.reply_to_message
    if not target:
        await message.reply("Reply to a message to warn that user.")
        return
    reason = (message.text or "").split(maxsplit=1)[1] if len((message.text or "").split()) > 1 else "No reason given"
    gs     = await GroupSettingsService.get_or_default(session, message.chat.id)
    count  = await WarnService.add(session, message.chat.id, target.from_user.id, reason)
    mention = _mention(target.from_user)
    if count >= gs.warn_limit:
        await WarnService.reset(session, message.chat.id, target.from_user.id)
        try:
            await bot.ban_chat_member(message.chat.id, target.from_user.id)
            await bot.unban_chat_member(message.chat.id, target.from_user.id)
        except TelegramBadRequest:
            pass
        await message.reply(f"🚫 {mention} removed after {count} warning(s). Reason: {reason}")
    else:
        await message.reply(f"⚠️ {mention} warned ({count}/{gs.warn_limit}). Reason: {reason}")


@router.message(Command("unwarn"), F.chat.type.in_({"group", "supergroup"}))
async def cmd_unwarn(message: Message, bot: Bot, session: AsyncSession):
    if not await _require_admin(bot, message.chat.id, message.from_user.id):
        return
    target = message.reply_to_message
    if not target:
        await message.reply("Reply to a message to clear that user's warnings.")
        return
    await WarnService.reset(session, message.chat.id, target.from_user.id)
    await message.reply(f"✅ Warnings cleared for {_mention(target.from_user)}.")


@router.message(Command("warnings"), F.chat.type.in_({"group", "supergroup"}))
async def cmd_warnings(message: Message, bot: Bot, session: AsyncSession):
    if not await _require_admin(bot, message.chat.id, message.from_user.id):
        return
    target = message.reply_to_message
    if not target:
        await message.reply("Reply to a message to check that user's warning count.")
        return
    count   = await WarnService.count(session, message.chat.id, target.from_user.id)
    gs      = await GroupSettingsService.get_or_default(session, message.chat.id)
    mention = _mention(target.from_user)
    await message.reply(f"ℹ️ {mention} has {count}/{gs.warn_limit} warning(s).")


@router.message(Command("kick"), F.chat.type.in_({"group", "supergroup"}))
async def cmd_kick(message: Message, bot: Bot):
    if not await _require_admin(bot, message.chat.id, message.from_user.id):
        return
    target = message.reply_to_message
    if not target:
        await message.reply("Reply to a message to kick that user.")
        return
    try:
        await bot.ban_chat_member(message.chat.id, target.from_user.id)
        await bot.unban_chat_member(message.chat.id, target.from_user.id)
        await message.reply(f"👢 {_mention(target.from_user)} was kicked.")
    except TelegramBadRequest as e:
        await message.reply(f"Could not kick: {e}")


@router.message(Command("ban"), F.chat.type.in_({"group", "supergroup"}))
async def cmd_ban(message: Message, bot: Bot):
    if not await _require_admin(bot, message.chat.id, message.from_user.id):
        return
    target = message.reply_to_message
    if not target:
        await message.reply("Reply to a message to ban that user.")
        return
    try:
        await bot.ban_chat_member(message.chat.id, target.from_user.id)
        await message.reply(f"🚫 {_mention(target.from_user)} was banned.")
    except TelegramBadRequest as e:
        await message.reply(f"Could not ban: {e}")