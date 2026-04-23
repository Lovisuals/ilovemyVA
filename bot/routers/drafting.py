from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from bot.models.bot_user import BotUser, UserRole
from bot.models.content_item import ContentItem, ContentBucket
from bot.states.draft_states import DraftingContent
from bot.services.content_service import ContentService

router = Router()

@router.message(Command("new"))
async def cmd_new_draft(message: Message, bot_user: BotUser, state: FSMContext):
    if bot_user.role not in [UserRole.SUPERADMIN, UserRole.ADMIN]:
        return
    await state.set_state(DraftingContent.WAITING_FOR_TEXT)
    await message.answer("📝 Send me the text for your new post:")

@router.message(DraftingContent.WAITING_FOR_TEXT)
async def on_text_received(message: Message, state: FSMContext, session: AsyncSession, bot_user: BotUser):
    await ContentService.create_item(
        session,
        bucket=ContentBucket.DRAFTS,
        text=message.text,
        created_by=bot_user.id
    )
    await message.answer("✅ Draft saved! View it in /content.")
    await state.clear()
