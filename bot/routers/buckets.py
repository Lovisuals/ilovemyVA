"bot/routers/buckets.py"

import uuid
from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.bot_user import BotUser, UserRole
from bot.models.content_item import ContentBucket
from bot.services.bucket_service import BucketService
from bot.keyboards.item_actions_kb import build_item_actions
from bot.strings import ITEM_DETAIL_HEADER, STORAGE_DELETE_CONFIRM, INVALID_ACTION

from bot.callbacks import ItemView, ItemArchive, ItemDelete

router = Router()

@router.callback_query(ItemView.filter())
async def on_item_view(query: CallbackQuery, callback_data: ItemView, bot_user: BotUser, session: AsyncSession):
    await query.answer()
    if bot_user.role not in [UserRole.SUPERADMIN, UserRole.ADMIN]:
        return

    item_id = uuid.UUID(callback_data.item_id)
    item = await BucketService.get_by_id(session, item_id)

    if not item:
        await query.message.answer(INVALID_ACTION)
        return

    text = item.text or "[Media Only]"
    header = ITEM_DETAIL_HEADER.format(id=str(item.id), bucket=item.bucket.value.capitalize())

    kb = build_item_actions(str(item.id), item.bucket.value)
    await query.message.edit_text(
        f"{header}\n\n{text}",
        reply_markup=kb
    )

@router.callback_query(ItemArchive.filter())
async def on_item_archive(query: CallbackQuery, callback_data: ItemArchive, bot_user: BotUser, session: AsyncSession):
    await query.answer("Item moved to Archive.")
    if bot_user.role not in [UserRole.SUPERADMIN, UserRole.ADMIN]:
        return

    item_id = uuid.UUID(callback_data.item_id)
    await BucketService.move_bucket(session, item_id, ContentBucket.ARCHIVE)

    # Refresh view
    item = await BucketService.get_by_id(session, item_id)
    kb = build_item_actions(str(item.id), item.bucket.value)
    await query.message.edit_reply_markup(reply_markup=kb)

@router.callback_query(ItemDelete.filter())
async def on_item_delete(query: CallbackQuery, callback_data: ItemDelete, bot_user: BotUser, session: AsyncSession):
    await query.answer()
    if bot_user.role not in [UserRole.SUPERADMIN, UserRole.ADMIN]:
        return

    item_id = uuid.UUID(callback_data.item_id)
    await BucketService.delete_item(session, item_id)
    await query.message.edit_text(STORAGE_DELETE_CONFIRM)
