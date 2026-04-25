from datetime import datetime, timezone
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from bot.models.audit_log import AuditLog
from bot.models.content_item import ContentItem, ContentBucket
from bot.models.bot_user import BotUser
from bot.models.connected_chat import ConnectedChat
from bot.config import settings

class SystemService:
    @staticmethod
    async def get_dashboard_data(session: AsyncSession, bot_username: str):
        db_status = "ONLINE"
        try:
            await session.execute(select(1))
        except Exception:
            db_status = "OFFLINE"

        stmt_scheduled = select(func.count()).select_from(ContentItem).where(ContentItem.bucket == ContentBucket.SCHEDULED)
        scheduled_count = (await session.execute(stmt_scheduled)).scalar() or 0

        stmt_drafts = select(func.count()).select_from(ContentItem).where(ContentItem.bucket == ContentBucket.DRAFTS)
        drafts_count = (await session.execute(stmt_drafts)).scalar() or 0

        stmt_users = select(func.count()).select_from(BotUser)
        users_count = (await session.execute(stmt_users)).scalar() or 0

        stmt_chats = select(func.count()).select_from(ConnectedChat)
        chats_count = (await session.execute(stmt_chats)).scalar() or 0

        stmt_audit = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(5)
        audit_logs = (await session.execute(stmt_audit)).scalars().all()
        
        audit_trail = ""
        for log in audit_logs:
            time_str = log.created_at.strftime("%H:%M")
            audit_trail += f"• [{time_str}] {log.event_code}\n"
        if not audit_trail:
            audit_trail = "No recent activity."

        vault_status = "LINKED"
        storage_vault = settings.bot.storage_channel_id or "Not Configured"
        if settings.bot.storage_channel_id:
            try:
                await session.execute(select(1))
            except Exception:
                vault_status = "STALL"
        else:
            vault_status = "OFFLINE"
        
        return {
            "db_status": db_status,
            "bot_username": bot_username,
            "scheduled": scheduled_count,
            "drafts": drafts_count,
            "users": users_count,
            "chats": chats_count,
            "audit_trail": audit_trail,
            "storage_vault": storage_vault,
            "vault_status": vault_status,
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        }
