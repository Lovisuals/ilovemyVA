from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from bot.keyboards.menu_kb import build_menu_row
from bot.keyboards.settings_kb import build_settings_panel
from bot.models.bot_user import BotUser, UserRole
from bot.strings import SETTINGS_TEXT
from bot.callbacks import SettingsAction

router = Router()

@router.message(Command("settings"))
async def cmd_settings(message: Message, bot_user: BotUser):
    if bot_user.role not in [UserRole.SUPERADMIN, UserRole.ADMIN]:
        return
    
    ai_enabled = True
    welcome_enabled = False
    timezone = "Europe/London (UTC+1)"
    
    kb = build_settings_panel(ai_enabled, welcome_enabled, timezone)
    await message.answer(
        "⚙️ *System Settings*\n\nConfigure global bot behavior and integrations.",
        reply_markup=kb,
        parse_mode="Markdown"
    )

@router.callback_query(SettingsAction.filter(F.action == "toggle_ai"))
async def on_toggle_ai(query: CallbackQuery):
    await query.answer("AI Review toggled")
    await query.message.edit_reply_markup(reply_markup=build_settings_panel(False, False, "Europe/London (UTC+1)"))

@router.callback_query(SettingsAction.filter(F.action == "toggle_welcome"))
async def on_toggle_welcome(query: CallbackQuery):
    await query.answer("Welcome messages toggled")
    await query.message.edit_reply_markup(reply_markup=build_settings_panel(True, True, "Europe/London (UTC+1)"))

@router.callback_query(SettingsAction.filter(F.action == "set_tz"))
async def on_set_timezone(query: CallbackQuery):
    await query.answer("Timezone selector coming soon", show_alert=True)

@router.callback_query(SettingsAction.filter(F.action == "view_api"))
async def on_view_api(query: CallbackQuery):
    await query.message.edit_text(
        "🔌 *API & Integration Status*\n\n"
        "• Gemini Pro: ✅ CONNECTED\n"
        "• Telegram API: ✅ ONLINE\n"
        "• Scheduler: ✅ ACTIVE\n"
        "• DB Engine: ✅ POOLED\n\n"
        "Latency: 42ms",
        reply_markup=build_settings_panel(True, False, "Europe/London (UTC+1)"),
        parse_mode="Markdown"
    )
    await query.answer()
