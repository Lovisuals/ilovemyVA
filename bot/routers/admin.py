from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.bot_user import BotUser, UserRole
from bot.models.content_item import ContentBucket
from bot.services.bucket_service import BucketService
from bot.keyboards.bucket_kb import build_bucket_panel
from bot.strings import ADMIN_PANEL_HEADER

from bot.callbacks import BucketSelect, BucketPage

router = Router()

@router.message(Command("admin"))
async def cmd_admin(message: Message, bot_user: BotUser, session: AsyncSession):
    if bot_user.role not in [UserRole.SUPERADMIN, UserRole.ADMIN]:
        return

    bucket = ContentBucket.DRAFTS
    items, total = await BucketService.get_page(session, bucket, 1, 10)
    total_pages = (total + 9) // 10

    kb = build_bucket_panel(bucket.value, items, 1, max(1, total_pages))
    await message.answer(
        ADMIN_PANEL_HEADER.format(bucket=bucket.value.capitalize()),
        reply_markup=kb
    )

@router.callback_query(BucketSelect.filter())
async def on_bucket_select(query: CallbackQuery, callback_data: BucketSelect, bot_user: BotUser, session: AsyncSession):
    await query.answer()
    if bot_user.role not in [UserRole.SUPERADMIN, UserRole.ADMIN]:
        return

    bucket_name = callback_data.bucket
    bucket = ContentBucket(bucket_name)

    items, total = await BucketService.get_page(session, bucket, 1, 10)
    total_pages = (total + 9) // 10

    kb = build_bucket_panel(bucket.value, items, 1, max(1, total_pages))
    await query.message.edit_text(
        ADMIN_PANEL_HEADER.format(bucket=bucket.value.capitalize()),
        reply_markup=kb
    )

@router.callback_query(BucketPage.filter())
async def on_bucket_page(query: CallbackQuery, callback_data: BucketPage, bot_user: BotUser, session: AsyncSession):
    await query.answer()
    if bot_user.role not in [UserRole.SUPERADMIN, UserRole.ADMIN]:
        return

    bucket_name = callback_data.bucket
    page = callback_data.page
    bucket = ContentBucket(bucket_name)

    items, total = await BucketService.get_page(session, bucket, page, 10)
    total_pages = (total + 9) // 10

    kb = build_bucket_panel(bucket.value, items, page, max(1, total_pages))
    await query.message.edit_text(
        ADMIN_PANEL_HEADER.format(bucket=bucket.value.capitalize()),
        reply_markup=kb
    )
