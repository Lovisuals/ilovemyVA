"bot/routers/admin.py"

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.bot_user import BotUser, UserRole
from bot.models.content_item import ContentBucket
from bot.services.bucket_service import BucketService
from bot.keyboards.bucket_kb import build_bucket_panel
from bot.strings import ADMIN_PANEL_HEADER

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

@router.callback_query(F.data.startswith("bucket_sel:"))
async def on_bucket_select(query: CallbackQuery, bot_user: BotUser, session: AsyncSession):
    if bot_user.role not in [UserRole.SUPERADMIN, UserRole.ADMIN]:
        return

    bucket_name = query.data.split(":")[1]
    bucket = ContentBucket(bucket_name)
    
    items, total = await BucketService.get_page(session, bucket, 1, 10)
    total_pages = (total + 9) // 10
    
    kb = build_bucket_panel(bucket.value, items, 1, max(1, total_pages))
    await query.message.edit_text(
        ADMIN_PANEL_HEADER.format(bucket=bucket.value.capitalize()),
        reply_markup=kb
    )
    await query.answer()

@router.callback_query(F.data.startswith("bucket_pg:"))
async def on_bucket_page(query: CallbackQuery, bot_user: BotUser, session: AsyncSession):
    if bot_user.role not in [UserRole.SUPERADMIN, UserRole.ADMIN]:
        return

    parts = query.data.split(":")
    bucket_name = parts[1]
    page = int(parts[2])
    bucket = ContentBucket(bucket_name)
    
    items, total = await BucketService.get_page(session, bucket, page, 10)
    total_pages = (total + 9) // 10
    
    kb = build_bucket_panel(bucket.value, items, page, max(1, total_pages))
    await query.message.edit_text(
        ADMIN_PANEL_HEADER.format(bucket=bucket.value.capitalize()),
        reply_markup=kb
    )
    await query.answer()
 Riverside is a 36 000+ member medical professional Telegram community. Professionalism is not optional. Security is not optional. Completeness is not optional.
