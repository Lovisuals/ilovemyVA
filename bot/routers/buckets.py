import uuid
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from bot.models.bot_user import BotUser, UserRole
from bot.models.content_item import ContentBucket
from bot.services.content_service import ContentService
from bot.keyboards.bucket_kb import build_bucket_list, build_content_list
from bot.keyboards.item_actions_kb import build_item_actions
from bot.strings import BUCKET_TITLE, ITEM_VIEW

router = Router()

@router.message(Command("content"))
async def cmd_content(message: Message, bot_user: BotUser):
    if bot_user.role not in [UserRole.SUPERADMIN, UserRole.ADMIN]:
        return
    kb = build_bucket_list()
    await message.answer("📁 **Content Management**", reply_markup=kb)

@router.callback_query(F.data.startswith("bkt_s:"))
async def on_bucket_select(query: CallbackQuery, bot_user: BotUser, session: AsyncSession):
    bucket = ContentBucket(query.data.split(":")[1])
    items, total = await ContentService.get_page(session, bucket, 1, 10)
    kb = build_content_list(items, bucket, 1, (total + 9) // 10)
    await query.message.edit_text(BUCKET_TITLE.format(bucket=bucket.value), reply_markup=kb)
    await query.answer()

@router.callback_query(F.data.startswith("item_ac:"))
async def on_item_action(query: CallbackQuery, bot_user: BotUser, session: AsyncSession):
    parts = query.data.split(":")
    item_id = uuid.UUID(parts[1])
    action = parts[2]
    if action == "view":
        item = await ContentService.get_by_id(session, item_id)
        if item:
            kb = build_item_actions(str(item.id), item.bucket)
            await query.message.edit_text(
                ITEM_VIEW.format(text=item.text or "No text", bucket=item.bucket.value),
                reply_markup=kb
            )
    elif action == "delete":
        await ContentService.delete_item(session, item_id)
        await query.answer("Item deleted.")
        await query.message.delete()
    elif action == "back":
        kb = build_bucket_list()
        await query.message.edit_text("📁 **Content Management**", reply_markup=kb)
    await query.answer()
