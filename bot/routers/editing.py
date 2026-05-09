import uuid
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from bot.models.bot_user import BotUser, UserRole
from bot.states.draft_states import DraftEditing
from bot.services.bucket_service import BucketService
from bot.services.agent_service import AgentService
from bot.keyboards.item_actions_kb import build_item_actions
from bot.callbacks import ItemEdit
router = Router()
@router.callback_query(ItemEdit.filter())
async def on_item_edit_start(
    query: CallbackQuery,
    callback_data: ItemEdit,
    bot_user: BotUser,
    state: FSMContext,
    session: AsyncSession
):
    if bot_user.role not in [UserRole.SUPERADMIN, UserRole.ADMIN]:
        return
    item_id = callback_data.item_id
    item = await BucketService.get_by_id(session, uuid.UUID(item_id))
    if not item:
        await query.answer("Item not found.", show_alert=True)
        return
    await state.update_data(edit_item_id=item_id)
    from bot.models.content_item import ContentBucket
    if item.bucket == ContentBucket.SCHEDULED:
        await state.set_state(DraftEditing.EDITING_TEXT)
        await query.message.edit_text(
            f"Current content (tap to copy):\n\n<code>{item.text}</code>\n\n"
            "Send the adjusted text below.",
            parse_mode="HTML"
        )
    else:
        await state.set_state(DraftEditing.SELECTING_FIELD)
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Edit Text", callback_data="edit_text")],
            [InlineKeyboardButton(text="Edit Tags", callback_data="edit_tags")],
            [InlineKeyboardButton(text="Cancel", callback_data=f"item_vw:{item_id}")]
        ])
        await query.message.edit_text("What would you like to modify?", reply_markup=kb)
    await query.answer()
@router.callback_query(DraftEditing.SELECTING_FIELD, F.data == "edit_text")
async def on_edit_text_start(query: CallbackQuery, state: FSMContext):
    await state.set_state(DraftEditing.EDITING_TEXT)
    await query.message.edit_text("Please send the new text for this content item.")
    await query.answer()
@router.message(DraftEditing.EDITING_TEXT)
async def on_edit_text_submit(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    item_id = uuid.UUID(data["edit_item_id"])
    item = await BucketService.get_by_id(session, item_id)
    if item:
        item.text = message.text
        tone_result = await AgentService.run_tone_check(message.text)
        item.tone_score = tone_result.score
        item.tone_flags = tone_result.flags
        # SIDE EFFECT: Commits modified content text to database. Why necessary and unavoidable: Ensures user edits are persisted for future publication or review.
        await session.commit()
        kb = build_item_actions(str(item.id), item.bucket)
        await message.answer(f" Text updated successfully for item `{item_id}`", reply_markup=kb)
    await state.clear()
@router.callback_query(DraftEditing.SELECTING_FIELD, F.data == "edit_tags")
async def on_edit_tags_start(query: CallbackQuery, state: FSMContext):
    await state.set_state(DraftEditing.EDITING_TAGS)
    await query.message.edit_text("Please send the new tags for this content item (comma-separated).")
    await query.answer()
@router.message(DraftEditing.EDITING_TAGS)
async def on_edit_tags_submit(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    item_id = uuid.UUID(data["edit_item_id"])
    item = await BucketService.get_by_id(session, item_id)
    if item:
        tags = [t.strip() for t in message.text.split(",") if t.strip()]
        item.tags = tags
        # SIDE EFFECT: Commits modified content tags to database. Why necessary and unavoidable: Ensures classification changes are persisted.
        await session.commit()
        kb = build_item_actions(str(item.id), item.bucket)
        await message.answer(f" Tags updated successfully for item `{item_id}`", reply_markup=kb)
    await state.clear()
