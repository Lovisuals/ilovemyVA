import logging
import asyncio
import contextlib
from urllib.parse import quote
from typing import Any, Awaitable, Callable, Dict

from aiohttp import web
from aiogram import Bot, Dispatcher, BaseMiddleware
from aiogram.types import Update
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from alembic.config import Config
from alembic import command

from bot.config import settings
from bot.strings import BOT_ONLINE
from bot.routers import onboarding, admin, user_management, buckets, drafting
from bot.routers import editing, scheduling, broadcast, moderation
from bot.routers import settings as settings_router
from bot.routers import menu as menu_router
from bot.routers import persona as persona_router
from bot.routers import faq as faq_router
from bot.routers import welcome_config as welcome_router
from bot.routers import chat_tracker as chat_tracker_router
from bot.routers import automod as automod_router
from bot.routers import group_admin as group_admin_router
from bot.middlewares.auth import AuthMiddleware
from bot.middlewares.db_session import DbSessionMiddleware
from bot.middlewares.rate_limit import RateLimitMiddleware
from bot.middlewares.logging_mw import LoggingMiddleware
from bot.middlewares.error_handler import ErrorHandlerMiddleware
from bot.scheduler.setup import setup_scheduler
from bot.utils.debug_log import write_debug_log

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

WEBHOOK_SECRET = settings.bot.webhook_secret


def run_migrations():
    try:
        cfg = Config("alembic.ini")
        command.upgrade(cfg, "head")
    except Exception as e:
        logger.error("Migration failed — bot may be unstable: %s", e, exc_info=True)


async def _deferred_startup(bot: Bot, dp: Dispatcher):
    logger.info("STARTUP: Waiting 5s for web server stability...")
    await asyncio.sleep(5)
    
    logger.info("STARTUP: Running deferred startup tasks...")
    
    # 1. Register Webhook/Polling IMMEDIATELY so the bot is "online"
    try:
        if settings.bot.webhook_url:
            base_url = settings.bot.webhook_url.rstrip("/")
            webhook_path = "/webhook/main"
            # #region agent log
            write_debug_log(
                run_id="pre-fix",
                hypothesis_id="H1",
                location="bot/main.py:_deferred_startup",
                message="Attempting webhook registration",
                data={"mode": "webhook", "base_url": base_url, "path": webhook_path},
            )
            # #endregion
            await asyncio.wait_for(bot.set_webhook(
                url=f"{base_url}{webhook_path}",
                secret_token=WEBHOOK_SECRET,
                drop_pending_updates=True,
                allowed_updates=["message", "callback_query", "channel_post", "chat_member", "my_chat_member"],
            ), timeout=15.0)
            logger.info("STARTUP: Webhook registered at %s%s", base_url, webhook_path)
            try:
                me = await asyncio.wait_for(bot.get_me(), timeout=10.0)
                logger.info("STARTUP: Bot identity username=@%s id=%s", me.username, me.id)
            except Exception as me_err:
                logger.warning("STARTUP: Failed to fetch bot identity: %s", me_err)
            try:
                webhook_info = await asyncio.wait_for(bot.get_webhook_info(), timeout=10.0)
                logger.info(
                    "STARTUP: Webhook info url=%s pending=%s last_error_date=%s last_error_message=%s",
                    webhook_info.url,
                    webhook_info.pending_update_count,
                    webhook_info.last_error_date,
                    webhook_info.last_error_message,
                )
            except Exception as webhook_info_err:
                logger.warning("STARTUP: Failed to fetch webhook info: %s", webhook_info_err)
            # #region agent log
            write_debug_log(
                run_id="pre-fix",
                hypothesis_id="H1",
                location="bot/main.py:_deferred_startup",
                message="Webhook registered successfully",
                data={"mode": "webhook", "base_url": base_url, "path": webhook_path},
            )
            # #endregion
        else:
            # #region agent log
            write_debug_log(
                run_id="pre-fix",
                hypothesis_id="H1",
                location="bot/main.py:_deferred_startup",
                message="Attempting polling startup",
                data={"mode": "polling"},
            )
            # #endregion
            await asyncio.wait_for(bot.delete_webhook(drop_pending_updates=True), timeout=10.0)
            asyncio.create_task(dp.start_polling(bot))
            logger.info("STARTUP: Polling started.")
            # #region agent log
            write_debug_log(
                run_id="pre-fix",
                hypothesis_id="H1",
                location="bot/main.py:_deferred_startup",
                message="Polling started successfully",
                data={"mode": "polling"},
            )
            # #endregion
    except Exception as e:
        logger.error("STARTUP: Webhook/Polling registration FAIL: %s", e)
        # #region agent log
        write_debug_log(
            run_id="pre-fix",
            hypothesis_id="H1",
            location="bot/main.py:_deferred_startup",
            message="Webhook/polling registration failed",
            data={"error": str(e), "mode": "webhook" if settings.bot.webhook_url else "polling"},
        )
        # #endregion

    logger.info("STARTUP: Starting database migrations...")
    try:
        cfg = Config("alembic.ini")
        await asyncio.wait_for(
            asyncio.to_thread(command.upgrade, cfg, "head"),
            timeout=120.0
        )
        logger.info("STARTUP: Migrations applied successfully.")
    except asyncio.TimeoutError:
        logger.error("STARTUP: Migration TIMEOUT after 120s — proceeding anyway")
    except Exception as e:
        logger.error("STARTUP: Migration FAILED: %s", e, exc_info=True)

    try:
        from aiogram.types import BotCommand, BotCommandScopeAllPrivateChats
        await asyncio.wait_for(bot.set_my_commands(
            [
                BotCommand(command="start",    description="Open main menu"),
                BotCommand(command="menu",     description="Main menu"),
                BotCommand(command="new",      description="Create a new post"),
                BotCommand(command="content",  description="Content library"),
                BotCommand(command="users",    description="Manage team"),
                BotCommand(command="settings", description="Settings"),
                BotCommand(command="admin",    description="Control centre"),
            ],
            scope=BotCommandScopeAllPrivateChats(),
        ), timeout=10.0)
        logger.info("STARTUP: Bot commands registered.")
    except Exception as e:
        logger.warning("STARTUP: Failed to register commands: %s", e)

    try:
        scheduler = await asyncio.wait_for(setup_scheduler(), timeout=15.0)
        dp["scheduler"] = scheduler
        await asyncio.wait_for(scheduler.start(), timeout=15.0)
        logger.info("STARTUP: Scheduler is now active.")
    except (Exception, asyncio.TimeoutError) as e:
        logger.warning("STARTUP: Scheduler failed to start: %s", e)

    try:
        await bot.send_message(settings.bot.owner_id, f"✅ **MedLocum Bot Online**\nVersion: 1.4.5\nStatus: Active")
    except Exception as e:
        logger.warning("STARTUP: Failed to notify owner: %s", e)

    try:
        watchdog_task = asyncio.create_task(_runtime_watchdog(bot))
        dp["watchdog_task"] = watchdog_task
        logger.info("STARTUP: Runtime watchdog started.")
    except Exception as e:
        logger.warning("STARTUP: Failed to start watchdog: %s", e)


async def _runtime_watchdog(bot: Bot):
    while True:
        try:
            webhook_info = await asyncio.wait_for(bot.get_webhook_info(), timeout=10.0)
            me = await asyncio.wait_for(bot.get_me(), timeout=10.0)
            logger.info(
                "WATCHDOG: bot=@%s pending=%s last_error_date=%s last_error_message=%s",
                me.username,
                webhook_info.pending_update_count,
                webhook_info.last_error_date,
                webhook_info.last_error_message,
            )
        except Exception as e:
            logger.warning("WATCHDOG: failed to fetch bot/webhook status: %s", e)
        await asyncio.sleep(30)


async def on_startup(bot: Bot, **kwargs):
    dp = kwargs.get("dispatcher")
    asyncio.create_task(_deferred_startup(bot, dp))


async def on_shutdown(bot: Bot, **kwargs):
    dp = kwargs.get("dispatcher")
    try:
        watchdog_task = dp.get("watchdog_task") if dp else None
        if watchdog_task:
            watchdog_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await watchdog_task
    except Exception:
        pass
    try:
        scheduler = dp.get("scheduler") if dp else None
        if scheduler:
            await scheduler.stop()
    except Exception:
        pass
    try:
        await bot.delete_webhook()
    except Exception:
        pass


async def health_check(_request: web.Request) -> web.Response:
    return web.json_response({"status": "ok", "version": "1.4.5"})


async def editor_handler(_request: web.Request) -> web.Response:
    api_base = (settings.bot.webhook_url or "").rstrip("/")
    with open("static/editor.html", "r", encoding="utf-8") as f:
        html = f.read()
    injection = f'<script>window.__API_BASE__ = "{api_base}";</script>'
    html = html.replace("</head>", f"{injection}\n</head>", 1)
    return web.Response(text=html, content_type="text/html", charset="utf-8")


@web.middleware
async def request_trace_middleware(request: web.Request, handler):
    if request.path == "/webhook/main":
        logger.info(
            "WEBHOOK: inbound request method=%s remote=%s ua=%s",
            request.method,
            request.remote,
            request.headers.get("User-Agent"),
        )
    return await handler(request)


def main():
    logger.info("MAIN: Starting bot initialization...")
    # #region agent log
    write_debug_log(
        run_id="pre-fix",
        hypothesis_id="H8",
        location="bot/main.py:main",
        message="Bot main() entered",
        data={"webhook_url_configured": bool(settings.bot.webhook_url), "port": settings.bot.port},
    )
    # #endregion
    # Migrations moved to _deferred_startup to avoid blocking web server start
    
    bot = Bot(token=settings.bot.token)
    dp = Dispatcher()
    
    logger.info("MAIN: Including routers...")
    dp.include_routers(
        chat_tracker_router.router,
        automod_router.router,
        group_admin_router.router,
        menu_router.router,
        persona_router.router,
        faq_router.router,
        welcome_router.router,
        onboarding.router, admin.router, user_management.router,
        buckets.router, drafting.router, editing.router,
        scheduling.router, broadcast.router, settings_router.router,
        moderation.router,
    )
    
    dp.update.outer_middleware(ErrorHandlerMiddleware())
    dp.update.outer_middleware(LoggingMiddleware())
    dp.update.outer_middleware(DbSessionMiddleware())
    dp.update.outer_middleware(RateLimitMiddleware())
    dp.update.outer_middleware(AuthMiddleware())
    
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    app = web.Application()
    app.middlewares.append(request_trace_middleware)
    app.router.add_get("/health", health_check)
    app.router.add_get("/static/editor.html", editor_handler)
    app.router.add_static("/static", path="static", name="static")
    app.router.add_post("/api/draft", drafting.api_draft_handler)

    if settings.bot.webhook_url:
        webhook_path = "/webhook/main"
        logger.info("Starting in webhook mode on port %s (Path: %s)", settings.bot.port, webhook_path)
        SimpleRequestHandler(
            dispatcher=dp, bot=bot, secret_token=WEBHOOK_SECRET
        ).register(app, path=webhook_path)
    else:
        logger.info("Starting in polling mode (with healthcheck server)")

    setup_application(app, dp, bot=bot)
    logger.info("MAIN: Handlers configured. Starting web server...")
    web.run_app(app, host="0.0.0.0", port=settings.bot.port)


if __name__ == "__main__":
    main()
