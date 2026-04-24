import json
import logging
import re
import time

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.services.group_settings_service import GroupSettingsService, WarnService

logger = logging.getLogger(__name__)
router = Router()

_URL_RE = re.compile(
    r"(https?://|t\.me/|@\w{5,}|"
    r"[\w\-]{2,}\.(com|org|net|io|app|ru|uk|info|biz|xyz)\b)",
    re.IGNORECASE,
)

_admin_cache: dict[tuple[int, int], tuple[bool, float]] = {}
_CACHE_TTL = 120


async def _is_admin(bot: Bot, chat_id: int, user_id: int) -> bool:
    now  = time.monotonic()
    key  = (chat_id, user_id)
    hit  = _admin_cache.get(key)
    if hit and now < hit[1]:
        return hit[0]
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        result = member.status in ("administrator", "creator")
    except Exception:
        result = False
    _admin_cache[key] = (result, now + _CACHE_TTL)
    return result


async def _warn_and_maybe_kick(
    bot: Bot, session: AsyncSession,
    message: Message, reason: str, warn_limit: int,
) -> None:
    chat_id = message.chat.id
    user    = message.from_user
    count   = await WarnService.add(session, chat_id, user.id, reason)
    mention = f"@{user.username}" if user.username else user.full_name

    try:
        await message.delete()
    except TelegramBadRequest:
        pass

    if count >= warn_limit:
        await WarnService.reset(session, chat_id, user.id)
        try:
            await bot.ban_chat_member(chat_id, user.id)
            await bot.unban_chat_member(chat_id, user.id)
        except TelegramBadRequest:
            pass
        await bot.send_message(
            chat_id,
            f"🚫 {mention} has been removed after {count} warning(s). Reason: {reason}",
        )
    else:
        await bot.send_message(
            chat_id,
            f"⚠️ {mention} — {reason}\n"
            f"Warning {count}/{warn_limit}. Reach the limit to be removed.",
        )


@router.message(
    F.chat.type.in_({"group", "supergroup"}),
    F.from_user.is_bot == False,  # noqa: E712
)
async def automod_filter(message: Message, bot: Bot, session: AsyncSession) -> None:
    gs = await GroupSettingsService.get(session, message.chat.id)
    if not gs or not gs.mod_enabled:
        return

    if await _is_admin(bot, message.chat.id, message.from_user.id):
        return

    text = message.text or message.caption or ""

    if gs.link_filter and _URL_RE.search(text):
        await _warn_and_maybe_kick(bot, session, message, "links are not allowed here", gs.warn_limit)
        return

    if gs.keyword_list:
        try:
            keywords = json.loads(gs.keyword_list)
        except Exception:
            keywords = []
        for kw in keywords:
            if kw and re.search(r"\b" + re.escape(kw) + r"\b", text, re.IGNORECASE):
                await _warn_and_maybe_kick(
                    bot, session, message,
                    f'"{kw}" is a banned term in this group',
                    gs.warn_limit,
                )
                return