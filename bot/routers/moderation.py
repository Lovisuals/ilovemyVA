from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from bot.models.moderation_event import ModerationEvent, ModerationResolution
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
    await query.message.edit_text(MODERATION_RESOLVED.format(res=event.resolution.value))
    await query.answer()
