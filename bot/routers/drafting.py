from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from bot.callbacks import NavData
from bot.keyboards.menu_kb import build_main_menu
from bot.models.bot_user import BotUser, UserRole
from bot.models.content_item import ContentBucket
from bot.services.content_service import ContentService
from bot.states.draft_states import DraftCreation
from bot.strings import DRAFT_PROMPT, MENU_ADMIN

router = Router()


@router.message(Command("new"))
async def cmd_new_draft(message: Message, bot_user: BotUser, state: FSMContext):
    if bot_user.role not in [UserRole.SUPERADMIN, UserRole.ADMIN]:
        return
    await state.set_state(DraftCreation.WAITING_CONTENT)
    builder = InlineKeyboardBuilder()
    builder.button(text="← Cancel", callback_data=NavData(section="menu").pack())
    await message.answer(DRAFT_PROMPT, reply_markup=builder.as_markup())


@router.message(DraftCreation.WAITING_CONTENT)
async def on_text_received(message: Message, state: FSMContext, session: AsyncSession, bot_user: BotUser):
    await ContentService.create_item(
        session,
        bucket=ContentBucket.DRAFTS,
        text=message.text,
        created_by=bot_user.id,
    )
    await state.clear()
    await message.answer(
        "✅ Draft saved.\n\n" + MENU_ADMIN,
        reply_markup=build_main_menu(bot_user.role),
    )
