import logging
import os
import secrets
import asyncio
from urllib.parse import quote
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.types import Update
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from alembic.config import Config
from alembic import command
from bot.config import settings
from bot.strings import BOT_ONLINE, BOT_SHUTDOWN
from bot.routers import (
    onboarding, admin, user_management, buckets,
    drafting, editing, scheduling, broadcast,
    settings as settings_router, moderation
)
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
    print("DEBUG: Starting database migrations...")
    try:
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
        print("DEBUG: Database migrations completed successfully.")
    except Exception as e:
        print(f"ERROR: Migration failed: {e}")
    finally:
        print("DEBUG: Exiting run_migrations()")

async def on_startup(bot: Bot, **kwargs):
    logger.info("Bot starting up...")
    webhook_url = settings.bot.webhook_url
    if webhook_url:
        logger.info(f"Setting up webhook at {webhook_url}")
        await bot.set_webhook(
            url=f"{webhook_url}/webhook/{quote(settings.bot.token, safe='')}",
            secret_token=WEBHOOK_SECRET,
            drop_pending_updates=True,
            allowed_updates=["message", "callback_query", "channel_post"]
        )
    else:
        logger.info("No webhook URL, deleting existing webhook for polling")
        await bot.delete_webhook(drop_pending_updates=True)
    
    logger.info("Initializing scheduler...")
    scheduler = await setup_scheduler()
    bot["scheduler"] = scheduler
    
    await scheduler.start()
    logger.info("Scheduler started.")
    
    try:
        await bot.send_message(settings.bot.owner_id, BOT_ONLINE)
        logger.info(f"Sent online notification to owner {settings.bot.owner_id}")
    except Exception as e:
        logger.warning(f"Could not send online notification to owner: {e}")

async def on_shutdown(bot: Bot, **kwargs):
    logger.info("Bot shutting down...")
    try:
        await bot.send_message(settings.bot.owner_id, BOT_SHUTDOWN)
    except Exception:
        pass
    scheduler = bot.get("scheduler")
    if scheduler:
        await scheduler.stop()
    await bot.delete_webhook()
    logger.info("Shutdown complete.")

async def health_check(request):
    return web.json_response({"status": "ok", "version": "1.3"})

def main():
    logger.info("Initializing bot and dispatcher...")
    run_migrations()
    bot = Bot(token=settings.bot.token)
    dp = Dispatcher()
    dp.include_routers(
        onboarding.router,
        admin.router,
        user_management.router,
        buckets.router,
        drafting.router,
        editing.router,
        scheduling.router,
        broadcast.router,
        settings_router.router,
        moderation.router
    )
    dp.update.outer_middleware(LoggingMiddleware())
    dp.update.outer_middleware(DbSessionMiddleware())
    dp.update.outer_middleware(RateLimitMiddleware())
    dp.update.outer_middleware(AuthMiddleware())
    dp.update.outer_middleware(ErrorHandlerMiddleware())
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    if settings.bot.webhook_url:
        logger.info("Starting Webhook mode...")
        app = web.Application()
        app.router.add_get("/health", health_check)
        async def webhook_handler(request: web.Request) -> web.Response:
            if request.headers.get("X-Telegram-Bot-Api-Secret-Token") != WEBHOOK_SECRET:
                return web.Response(status=403)
            return await SimpleRequestHandler(dispatcher=dp, bot=bot).handle(request)
        app.router.add_post(f"/webhook/{quote(settings.bot.token, safe='')}", webhook_handler)
        setup_application(app, dp, bot=bot)
        web.run_app(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
    else:
        logger.info("Starting Polling mode...")
        asyncio.run(dp.start_polling(bot))

if __name__ == "__main__":
    main()
