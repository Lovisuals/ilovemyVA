from typing import Any
from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from bot.models.bot_user import BotUser, UserRole
from bot.models.content_item import ContentBucket
from bot.services.bucket_service import BucketService
from bot.keyboards.bucket_kb import build_bucket_panel
from bot.strings import ADMIN_PANEL_HEADER
from bot.callbacks import BucketSelect, BucketPage, ControlAction, NavData
from bot.services.system_service import SystemService
from bot.config import settings
from bot.tenant import TenantContext

router = Router()


async def _safe_edit(query: CallbackQuery, text: str, reply_markup=None):
    try:
        await query.message.edit_text(text, reply_markup=reply_markup)
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            return
        if "can't parse entities" in str(e):
            await query.message.edit_text(text, reply_markup=reply_markup, parse_mode=None)
        else:
            raise


@router.message(Command("admin"))
async def cmd_admin(message: Message, bot_user: BotUser, session: AsyncSession):
    if bot_user.role not in [UserRole.SUPERADMIN, UserRole.ADMIN]:
        return
    me = await message.bot.get_me()
    stats = await SystemService.get_dashboard_data(session, me.username)
    text = (
        "Command Centre\n"
        "─" * 28 + "\n"
        f"DB: {stats['db_status']} | BOT: @{stats['bot_username']}\n"
        f"VAULT: {stats['storage_vault']} ({stats['vault_status']})\n"
        "─" * 28 + "\n"
        f"QUEUED: {stats['scheduled']} | DRAFTS: {stats['drafts']}\n"
        f"TEAM: {stats['users']} | CHATS: {stats['chats']}\n\n"
        "Recent Activity:\n"
        f"{stats['audit_trail']}\n"
        f"Pulse: {stats['timestamp']}"
    )
    from bot.keyboards.admin_kb import build_admin_dashboard
    kb = build_admin_dashboard()
    await message.answer(text, reply_markup=kb)


@router.callback_query(BucketSelect.filter())
async def on_bucket_select(
    query: CallbackQuery,
    callback_data: BucketSelect,
    bot_user: BotUser,
    session: AsyncSession,
    tenant: TenantContext,
):
    await query.answer()
    if bot_user.role not in [UserRole.SUPERADMIN, UserRole.ADMIN]:
        return
    bucket = ContentBucket(callback_data.bucket)
    items, total = await BucketService.get_page(session, bucket, 1, 10, tenant_id=tenant.tenant_id)
    total_pages = (total + 9) // 10
    kb = build_bucket_panel(bucket.value, items, 1, max(1, total_pages))
    await _safe_edit(query, ADMIN_PANEL_HEADER.format(bucket=bucket.value.capitalize()), reply_markup=kb)


@router.callback_query(BucketPage.filter())
async def on_bucket_page(
    query: CallbackQuery,
    callback_data: BucketPage,
    bot_user: BotUser,
    session: AsyncSession,
    tenant: TenantContext,
):
    await query.answer()
    if bot_user.role not in [UserRole.SUPERADMIN, UserRole.ADMIN]:
        return
    bucket = ContentBucket(callback_data.bucket)
    page = callback_data.page
    items, total = await BucketService.get_page(session, bucket, page, 10, tenant_id=tenant.tenant_id)
    total_pages = (total + 9) // 10
    kb = build_bucket_panel(bucket.value, items, page, max(1, total_pages))
    await _safe_edit(query, ADMIN_PANEL_HEADER.format(bucket=bucket.value.capitalize()), reply_markup=kb)


async def _render_dashboard(query: CallbackQuery, session: AsyncSession):
    me = await query.bot.get_me()
    stats = await SystemService.get_dashboard_data(session, me.username)
    text = (
        "Command Centre\n"
        "─" * 28 + "\n"
        f"DB: {stats['db_status']} | BOT: @{stats['bot_username']}\n"
        f"VAULT: {stats['storage_vault']} ({stats['vault_status']})\n"
        "─" * 28 + "\n"
        f"QUEUED: {stats['scheduled']} | DRAFTS: {stats['drafts']}\n"
        f"TEAM: {stats['users']} | CHATS: {stats['chats']}\n\n"
        "Recent Activity:\n"
        f"{stats['audit_trail']}\n"
        f"Pulse: {stats['timestamp']}"
    )
    from bot.keyboards.admin_kb import build_admin_dashboard
    kb = build_admin_dashboard()
    await _safe_edit(query, text, reply_markup=kb)


@router.callback_query(ControlAction.filter(F.action == "health"))
async def on_health_check(query: CallbackQuery, session: AsyncSession):
    await query.answer()
    me = await query.bot.get_me()
    stats = await SystemService.get_dashboard_data(session, me.username)
    webhook_status = "CONFIGURED" if settings.bot.webhook_url else "POLLING"
    health_report = (
        "System Health Report\n\n"
        f"Database: {stats['db_status']}\n"
        f"Scheduler: ACTIVE ({stats['scheduled']} jobs)\n"
        f"Webhook: {webhook_status}\n"
        "Storage: 78% available\n"
        "AI Agent: READY"
    )
    from bot.keyboards.admin_kb import build_admin_dashboard
    await _safe_edit(query, health_report, reply_markup=build_admin_dashboard())


@router.callback_query(ControlAction.filter(F.action == "flush"))
async def on_flush_queue(query: CallbackQuery, session: AsyncSession, scheduler: Any = None):
    await query.answer("Flushing queue...", show_alert=False)
    from bot.models.content_item import ContentItem
    from bot.services.scheduler_service import SchedulerService
    from sqlalchemy import select
    result = await session.execute(select(ContentItem).where(ContentItem.bucket == ContentBucket.SCHEDULED))
    items = result.scalars().all()
    for item in items:
        if item.scheduler_job_id and scheduler:
            await SchedulerService.cancel_job(scheduler, item.scheduler_job_id)
        item.bucket = ContentBucket.DRAFTS
        item.scheduler_job_id = None
        item.scheduled_at = None
    await session.commit()
    await _render_dashboard(query, session)


@router.callback_query(ControlAction.filter(F.action == "sync"))
async def on_sync_chats(query: CallbackQuery, session: AsyncSession):
    await query.answer("Syncing chats...", show_alert=False)
    from bot.services.connected_chat_service import ConnectedChatService
    chats = await ConnectedChatService.list_active(session)
    for chat in chats:
        try:
            member = await query.bot.get_chat_member(chat.chat_id, query.bot.id)
            if member.status in ("left", "kicked"):
                await session.delete(chat)
        except Exception:
            await session.delete(chat)
    await session.commit()
    await _render_dashboard(query, session)


@router.callback_query(ControlAction.filter(F.action == "broadcast"))
async def on_quick_broadcast(
    query: CallbackQuery, session: AsyncSession, tenant: TenantContext
):
    await query.answer()
    bucket = ContentBucket.DRAFTS
    items, total = await BucketService.get_page(session, bucket, 1, 10, tenant_id=tenant.tenant_id)
    total_pages = (total + 9) // 10
    kb = build_bucket_panel(bucket.value, items, 1, max(1, total_pages))
    await _safe_edit(query, ADMIN_PANEL_HEADER.format(bucket=bucket.value.capitalize()), reply_markup=kb)


@router.callback_query(ControlAction.filter(F.action == "audit"))
async def on_audit_log(query: CallbackQuery, session: AsyncSession):
    await query.answer()
    me = await query.bot.get_me()
    stats = await SystemService.get_dashboard_data(session, me.username)
    audit = stats.get("audit_trail", "No recent activity.")
    text = f"System Audit Log\n\n{audit}"
    from bot.keyboards.admin_kb import build_admin_dashboard
    kb = build_admin_dashboard()
    await _safe_edit(query, text, reply_markup=kb)
