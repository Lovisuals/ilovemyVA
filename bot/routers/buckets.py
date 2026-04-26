import uuid
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.callbacks import ContentItemAction
from bot.keyboards.bucket_kb import build_bucket_list, build_content_list
from bot.keyboards.item_actions_kb import build_item_actions
from bot.models.bot_user import BotUser, UserRole
from bot.models.content_item import ContentBucket
from bot.services.content_service import ContentService
from bot.strings import BUCKET_TITLE, ITEM_VIEW

router = Router()

@router.message(Command("content"))
async def cmd_content(message: Message, bot_user: BotUser):
    if bot_user.role not in [UserRole.SUPERADMIN, UserRole.ADMIN]:
        return
    await message.answer("📂 Content Library\n\nSelect a bucket:", reply_markup=build_bucket_list())

@router.callback_query(ContentItemAction.filter())
async def on_item_action(
    query: CallbackQuery, callback_data: ContentItemAction,
    bot_user: BotUser, session: AsyncSession
):
    item_id = uuid.UUID(callback_data.item_id)
    action  = callback_data.action

    if action == "view":
        await query.answer()
        item = await ContentService.get_by_id(session, item_id)
        if item:
            kb = build_item_actions(str(item.id), item.bucket)
            text = ITEM_VIEW.format(text=item.text or "No text", bucket=item.bucket.value)
            if item.subject:
                text = f"📌 {item.subject}\n\n" + text
            try:
                await query.message.edit_text(text, reply_markup=kb)
            except Exception:
                pass

    elif action == "delete":
        if bot_user.role not in [UserRole.SUPERADMIN, UserRole.ADMIN]:
            await query.answer()
            return
        await query.answer("Item deleted.")
        await ContentService.delete_item(session, item_id)
        kb = build_bucket_list()
        try:
            await query.message.edit_text("📂 Content Library\n\nSelect a bucket:", reply_markup=kb)
        except Exception:
            pass

    elif action == "back":
        await query.answer()
        item = await ContentService.get_by_id(session, item_id)
        bucket = item.bucket if item else ContentBucket.DRAFTS
        items, total = await ContentService.get_page(session, bucket, 1, 10)
        kb = build_content_list(items, bucket, 1, max(1, (total + 9) // 10))
        try:
            await query.message.edit_text(BUCKET_TITLE.format(bucket=bucket.value), reply_markup=kb)
        except Exception:
            pass

    else:
        await query.answer()
