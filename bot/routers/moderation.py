from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from bot.models.moderation_event import ModerationEvent, ModerationResolution, ModerationEventType
from bot.callbacks import ModerationResolve
from bot.strings import MODERATION_RESOLVED, INVALID_ACTION

router = Router()

@router.callback_query(ModerationResolve.filter())
async def on_moderation_resolve(
    query: CallbackQuery,
    callback_data: ModerationResolve,
    session: AsyncSession
):
    event_id = callback_data.event_id
    stmt = select(ModerationEvent).where(ModerationEvent.id == event_id)
    result = await session.execute(stmt)
    event = result.scalar_one_or_none()
    if not event:
        await query.answer(INVALID_ACTION)
        return
    event.resolved_by = query.from_user.id
    event.resolution = ModerationResolution(callback_data.resolution)
    await session.commit()
    
    enforcement_msg = ""
    if event.resolution == ModerationResolution.APPROVED:
        try:
            if event.event_type == ModerationEventType.BAN_REQUEST:
                await query.bot.ban_chat_member(event.chat_id, event.actor_user_id)
                enforcement_msg = " (User Banned)"
            elif event.event_type == ModerationEventType.DELETE:
                if event.message_id:
                    await query.bot.delete_message(event.chat_id, event.message_id)
                enforcement_msg = " (Message Deleted)"
            elif event.event_type == ModerationEventType.MUTE:
                from aiogram.types import ChatPermissions
                await query.bot.restrict_chat_member(
                    event.chat_id, 
                    event.actor_user_id, 
                    permissions=ChatPermissions(can_send_messages=False)
                )
                enforcement_msg = " (User Muted)"
        except Exception as e:
            enforcement_msg = f" (Enforcement failed: {str(e)})"

    await query.message.edit_text(
        MODERATION_RESOLVED.format(res=event.resolution.value) + enforcement_msg
    )
    await query.answer()
