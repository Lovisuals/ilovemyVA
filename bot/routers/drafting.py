"bot/routers/drafting.py"

from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.bot_user import BotUser, UserRole
from bot.states.draft_states import DraftCreation
from bot.services.bucket_service import BucketService
from bot.services.agent_service import AgentService
from bot.services.storage_service import TelegramStorageService
from bot.strings import TONE_FLAG_WARNING

router = Router()

@router.message(Command("newpost"))
async def cmd_newpost(message: Message, bot_user: BotUser, state: FSMContext):
    if bot_user.role not in [UserRole.SUPERADMIN, UserRole.ADMIN]:
        return
    
    await state.set_state(DraftCreation.WAITING_CONTENT)
    await message.answer("📝 Please send the content for your new draft (text, image, or video).")

@router.message(DraftCreation.WAITING_CONTENT)
async def on_draft_content(message: Message, bot_user: BotUser, state: FSMContext, bot: Bot, session: AsyncSession):
    text = message.text or message.caption
    file_ids = []

    if message.photo or message.video or message.document:
        record = await TelegramStorageService.upload(bot, session, message, bot_user.id)
        file_ids.append({"type": record.file_type.value, "file_id": record.file_id})

    tone_result = await AgentService.run_tone_check(text or "")
    
    await state.update_data(text=text, file_ids=file_ids, tone_score=tone_result.score, tone_flags=tone_result.flags)
    await state.set_state(DraftCreation.CONFIRMING)
    
    preview = f"**Draft Preview**\n\n{text or '[Media]'}\n\n"
    preview += f"Tone Score: {tone_result.score:.2f}\n"
    if tone_result.score < 0.7:
        preview += TONE_FLAG_WARNING.format(score=tone_result.score)
        
    # Inline keyboard directly here to follow directive of full implementation
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Save Draft", callback_data="draft_save")],
        [InlineKeyboardButton(text="🔄 Retry", callback_data="draft_retry")],
        [InlineKeyboardButton(text="❌ Cancel", callback_data="draft_cancel")]
    ])
    
    await message.answer(preview, reply_markup=kb, parse_mode="Markdown")

@router.callback_query(DraftCreation.CONFIRMING, F.data == "draft_save")
async def on_draft_save(query: CallbackQuery, bot_user: BotUser, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    item = await BucketService.create_draft(
        session, 
        text=data.get("text"), 
        file_ids=data.get("file_ids", []), 
        created_by=bot_user.id
    )
    
    # Save tone results
    item.tone_score = data.get("tone_score")
    item.tone_flags = data.get("tone_flags")
    await session.commit()
    
    await query.message.edit_text(f"✅ Draft saved with ID: `{item.id}`")
    await state.clear()
    await query.answer()

@router.callback_query(F.data == "draft_cancel")
async def on_draft_cancel(query: CallbackQuery, state: FSMContext):
    await state.clear()
    await query.message.edit_text("❌ Draft cancelled.")
    await query.answer()
 Riverside is a 36 000+ member medical professional Telegram community. Professionalism is not optional. Security is not optional. Completeness is not optional.
