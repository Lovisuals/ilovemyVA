import logging
import secrets
import asyncio
from urllib.parse import quote
from typing import Any, Awaitable, Callable, Dict

from aiohttp import web
from aiogram import Bot, Dispatcher, BaseMiddleware
from aiogram.types import Update
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from alembic.config import Config
from alembic import command

from bot.config import settings
from bot.strings import BOT_ONLINE, BOT_SHUTDOWN
from bot.routers import onboarding, admin, user_management, buckets, drafting
from bot.routers import editing, scheduling, broadcast, moderation
from bot.routers import settings as settings_router
from bot.routers import menu as menu_router
from bot.middlewares.auth import AuthMiddleware
from bot.middlewares.db_session import DbSessionMiddleware
from bot.middlewares.rate_limit import RateLimitMiddleware
from bot.middlewares.logging_mw import LoggingMiddleware
from bot.middlewares.error_handler import ErrorHandlerMiddleware
from bot.scheduler.setup import setup_scheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

WEBHOOK_SECRET = secrets.token_hex(32)


def run_migrations():
    try:
        cfg = Config("alembic.ini")
        command.upgrade(cfg, "head")
    except Exception as e:
        logger.warning("Migration error (non-blocking): %s", e)


async def _deferred_startup(bot: Bot):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, run_migrations)

    try:
        from aiogram.types import BotCommand, BotCommandScopeAllPrivateChats
        await bot.set_my_commands(
            [
                BotCommand(command="start",    description="Open main menu"),
                BotCommand(command="menu",     description="Main menu"),
                BotCommand(command="new",      description="Create a new draft"),
                BotCommand(command="content",  description="Content library"),
                BotCommand(command="users",    description="Manage team"),
                BotCommand(command="settings", description="Settings"),
                BotCommand(command="admin",    description="Control centre"),
            ],
            scope=BotCommandScopeAllPrivateChats(),
        )
    except Exception as e:
        logger.warning("Failed to register commands: %s", e)

    try:
        if settings.bot.webhook_url:
            await bot.set_webhook(
                url=f"{settings.bot.webhook_url}/webhook/{quote(settings.bot.token, safe='')}",
                secret_token=WEBHOOK_SECRET,
                drop_pending_updates=True,
                allowed_updates=["message", "callback_query", "channel_post"],
            )
        else:
            await bot.delete_webhook(drop_pending_updates=True)
    except Exception as e:
        logger.warning("Webhook configuration failed: %s", e)

    try:
        scheduler = await asyncio.wait_for(setup_scheduler(), timeout=10.0)
        bot["scheduler"] = scheduler
        await asyncio.wait_for(scheduler.start(), timeout=10.0)
    except (Exception, asyncio.TimeoutError) as e:
        logger.warning("Scheduler failed to start: %s", e)

    try:
        await bot.send_message(settings.bot.owner_id, BOT_ONLINE)
    except Exception as e:
        logger.warning("Failed to notify owner on startup: %s", e)


async def on_startup(bot: Bot, **kwargs):
    asyncio.create_task(_deferred_startup(bot))


async def on_shutdown(bot: Bot, **kwargs):
    try:
        await bot.send_message(settings.bot.owner_id, BOT_SHUTDOWN)
    except Exception:
        pass
    scheduler = bot.get("scheduler")
    if scheduler:
        await scheduler.stop()
    try:
        await bot.delete_webhook()
    except Exception:
        pass


async def health_check(_request: web.Request) -> web.Response:
    return web.json_response({"status": "ok", "version": "1.4"})


class BotInjectionMiddleware(BaseMiddleware):
    def __init__(self, bot: Bot):
        self.bot = bot

    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any],
    ) -> Any:
        data["bot"] = self.bot
        return await handler(event, data)


def main():
    bot = Bot(token=settings.bot.token)
    dp = Dispatcher()
    dp.include_routers(
        menu_router.router,
        onboarding.router, admin.router, user_management.router,
        buckets.router, drafting.router, editing.router,
        scheduling.router, broadcast.router, settings_router.router,
        moderation.router,
    )
    dp.update.outer_middleware(BotInjectionMiddleware(bot))
    dp.update.outer_middleware(ErrorHandlerMiddleware())
    dp.update.outer_middleware(LoggingMiddleware())
    dp.update.outer_middleware(DbSessionMiddleware())
    dp.update.outer_middleware(RateLimitMiddleware())
    dp.update.outer_middleware(AuthMiddleware())
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    if settings.bot.webhook_url:
        logger.info("Starting in webhook mode on port %s", settings.bot.port)
        app = web.Application()
        app.router.add_get("/health", health_check)
        SimpleRequestHandler(
            dispatcher=dp, bot=bot, secret_token=WEBHOOK_SECRET
        ).register(app, path=f"/webhook/{quote(settings.bot.token, safe='')}")
        setup_application(app, dp, bot=bot)
        web.run_app(app, host="0.0.0.0", port=settings.bot.port)
    else:
        logger.info("Starting in polling mode")
        asyncio.run(dp.start_polling(bot))


if __name__ == "__main__":
    main()
