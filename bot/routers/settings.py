from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from bot.keyboards.menu_kb import build_menu_row
from bot.keyboards.settings_kb import build_settings_panel
from bot.models.bot_user import BotUser, UserRole
from bot.callbacks import SettingsAction
router = Router()
@router.message(Command("settings"))
async def cmd_settings(message: Message, bot_user: BotUser):
    if bot_user.role not in [UserRole.SUPERADMIN, UserRole.ADMIN]:
        return
    kb = build_settings_panel(True, False, "Africa/Lagos")
    await message.answer(
        "️ *SYSTEM CONFIGURATION*\n"
        "─" * 20 + "\n"
        "Global parameters and operational toggles.",
        reply_markup=kb,
        parse_mode="Markdown"
    )
@router.callback_query(SettingsAction.filter(F.action == "toggle_ai"))
async def on_toggle_ai(query: CallbackQuery):
    await query.answer("Security Engine Toggled")
    await query.message.edit_reply_markup(reply_markup=build_settings_panel(False, False, "Africa/Lagos"))
@router.callback_query(SettingsAction.filter(F.action == "toggle_welcome"))
async def on_toggle_welcome(query: CallbackQuery):
    await query.answer("Welcome Protocol Toggled")
    await query.message.edit_reply_markup(reply_markup=build_settings_panel(True, True, "Africa/Lagos"))
@router.callback_query(SettingsAction.filter(F.action == "set_tz"))
async def on_set_timezone(query: CallbackQuery):
    await query.answer("Temporal sync initiated...", show_alert=True)
@router.callback_query(SettingsAction.filter(F.action == "view_api"))
async def on_view_api(query: CallbackQuery):
    await query.message.edit_text(
        " *SIGNAL & INTEGRATION PULSE*\n"
        "─" * 20 + "\n"
        "• Security Core:  ACTIVE\n"
        "• Telegram Uplink:  STABLE\n"
        "• Scheduler Job:  RUNNING\n"
        "• Vault Storage:  LINKED\n\n"
        "Latency: `24ms`",
        reply_markup=build_settings_panel(True, False, "Africa/Lagos"),
        parse_mode="Markdown"
    )
    await query.answer()
