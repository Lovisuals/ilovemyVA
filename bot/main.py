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

async def on_startup(bot: Bot, **kwargs):
    print("DEBUG: on_startup triggered")
    webhook_url = settings.bot.webhook_url
    if webhook_url:
        print(f"DEBUG: Setting up webhook at {webhook_url}")
        await bot.set_webhook(
            url=f"{webhook_url}/webhook/{quote(settings.bot.token, safe='')}",
            secret_token=WEBHOOK_SECRET,
            drop_pending_updates=True,
            allowed_updates=["message", "callback_query", "channel_post"]
        )
    else:
        print("DEBUG: Using polling mode")
        await bot.delete_webhook(drop_pending_updates=True)
    
    print("DEBUG: Setting up scheduler...")
    scheduler = await setup_scheduler()
    bot["scheduler"] = scheduler
    await scheduler.start()
    print("DEBUG: Scheduler started.")
    
    try:
        await bot.send_message(settings.bot.owner_id, BOT_ONLINE)
        print(f"DEBUG: Sent online notification to {settings.bot.owner_id}")
    except Exception as e:
        print(f"ERROR: Could not notify owner: {e}")

async def on_shutdown(bot: Bot, **kwargs):
    print("DEBUG: on_shutdown triggered")
    try:
        await bot.send_message(settings.bot.owner_id, BOT_SHUTDOWN)
    except Exception:
        pass
    scheduler = bot.get("scheduler")
    if scheduler:
        await scheduler.stop()
    await bot.delete_webhook()

async def health_check(request):
    return web.json_response({"status": "ok", "version": "1.3"})

def main():
    print("DEBUG: Entering main()")
    print(f"DEBUG: CONFIG - TOKEN: {settings.bot.token[:5]}***")
    print(f"DEBUG: CONFIG - OWNER: {settings.bot.owner_id}")
    print(f"DEBUG: CONFIG - STORAGE: {settings.bot.storage_channel_id}")
    print(f"DEBUG: CONFIG - MAIN: {settings.bot.main_channel_id}")
    
    import threading
    # SIDE EFFECT: Running migrations in background to prevent startup hang.
    threading.Thread(target=run_migrations, daemon=True).start()
    
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
        print("DEBUG: Starting in WEBHOOK mode")
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
        print("DEBUG: Starting in POLLING mode")
        asyncio.run(dp.start_polling(bot))

if __name__ == "__main__":
    main()




