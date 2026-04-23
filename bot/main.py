import sys
import logging
import os
import secrets
import asyncio
import threading
from urllib.parse import quote
from typing import Any, Awaitable, Callable, Dict
from aiohttp import web
from aiogram import Bot, Dispatcher, BaseMiddleware
from aiogram.types import Update
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from alembic.config import Config
from alembic import command

sys.stderr.write("DEBUG: main.py loading...\n")
sys.stderr.flush()

from bot.config import settings
from bot.strings import BOT_ONLINE, BOT_SHUTDOWN

sys.stderr.write("DEBUG: Importing routers...\n")
sys.stderr.flush()

from bot.routers import onboarding
from bot.routers import admin
from bot.routers import user_management
from bot.routers import buckets
from bot.routers import drafting
from bot.routers import editing
from bot.routers import scheduling
from bot.routers import broadcast
from bot.routers import settings as settings_router
from bot.routers import moderation
sys.stderr.write("DEBUG: All routers loaded\n")
sys.stderr.flush()

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
    sys.stderr.write("DEBUG: Starting migrations...\n")
    sys.stderr.flush()
    try:
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
        sys.stderr.write("DEBUG: Migrations OK\n")
    except Exception as e:
        sys.stderr.write(f"WARN: Migration error (non-blocking): {e}\n")
        sys.stderr.write("DEBUG: Continuing startup; tables may be created on first query\n")
    sys.stderr.flush()

async def defer_migrations():
    """Run migrations asynchronously in the background after startup."""
    await asyncio.sleep(1)
    run_migrations()

async def on_startup(bot: Bot, **kwargs):
    sys.stderr.write("DEBUG: on_startup triggered\n")
    sys.stderr.flush()
    
    # Run migrations in background without blocking
    try:
        run_migrations()
    except Exception as e:
        sys.stderr.write(f"WARN: Deferred migration failed: {e}\n")
        sys.stderr.flush()
    
    # Make all Telegram API calls non-fatal
    try:
        webhook_url = settings.bot.webhook_url
        if webhook_url:
            try:
                await bot.set_webhook(
                    url=f"{webhook_url}/webhook/{quote(settings.bot.token, safe='')}",
                    secret_token=WEBHOOK_SECRET,
                    drop_pending_updates=True,
                    allowed_updates=["message", "callback_query", "channel_post"]
                )
                sys.stderr.write("DEBUG: Webhook set\n")
            except Exception as e:
                sys.stderr.write(f"WARN: Failed to set webhook: {e}\n")
                sys.stderr.flush()
        else:
            try:
                await bot.delete_webhook(drop_pending_updates=True)
                sys.stderr.write("DEBUG: Webhook deleted\n")
            except Exception as e:
                sys.stderr.write(f"WARN: Failed to delete webhook: {e}\n")
                sys.stderr.flush()
    except Exception as e:
        sys.stderr.write(f"WARN: Webhook configuration failed: {e}\n")
        sys.stderr.flush()
    
    sys.stderr.write("DEBUG: Setting up scheduler...\n")
    sys.stderr.flush()
    try:
        scheduler = await setup_scheduler()
        bot["scheduler"] = scheduler
        await scheduler.start()
        sys.stderr.write("DEBUG: Scheduler started\n")
    except Exception as e:
        sys.stderr.write(f"WARN: Scheduler fail: {e}\n")
    sys.stderr.flush()
    
    try:
        await bot.send_message(settings.bot.owner_id, BOT_ONLINE)
        sys.stderr.write(f"DEBUG: Notified owner {settings.bot.owner_id}\n")
    except Exception as e:
        sys.stderr.write(f"WARN: Failed to notify owner: {e}\n")
    sys.stderr.flush()
    
    sys.stderr.write("DEBUG: Startup complete\n")
    sys.stderr.flush()

async def on_shutdown(bot: Bot, **kwargs):
    sys.stderr.write("DEBUG: on_shutdown\n")
    sys.stderr.flush()
    try:
        await bot.send_message(settings.bot.owner_id, BOT_SHUTDOWN)
    except Exception:
        pass
    scheduler = bot.get("scheduler")
    if scheduler:
        await scheduler.stop()
    await bot.delete_webhook()

async def health_check(request):
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
    sys.stderr.write("DEBUG: Entering main()\n")
    sys.stderr.write(f"DEBUG: TOKEN: {settings.bot.token[:5]}***\n")
    sys.stderr.flush()
    
    # Migrations run async after startup to avoid blocking
    
    bot = Bot(token=settings.bot.token)
    dp = Dispatcher()
    dp.include_routers(
        onboarding.router, admin.router, user_management.router,
        buckets.router, drafting.router, editing.router,
        scheduling.router, broadcast.router, settings_router.router,
        moderation.router
    )
    dp.update.outer_middleware(LoggingMiddleware())
    dp.update.outer_middleware(DbSessionMiddleware())
    dp.update.outer_middleware(RateLimitMiddleware())
    dp.update.outer_middleware(AuthMiddleware())
    dp.update.outer_middleware(ErrorHandlerMiddleware())
    dp.update.outer_middleware(BotInjectionMiddleware(bot))
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    try:
        if settings.bot.webhook_url:
            sys.stderr.write("DEBUG: WEBHOOK mode\n")
            sys.stderr.flush()
            app = web.Application()
            app.router.add_get("/health", health_check)
            async def webhook_handler(request: web.Request) -> web.Response:
                if request.headers.get("X-Telegram-Bot-Api-Secret-Token") != WEBHOOK_SECRET:
                    return web.Response(status=403)
                return await SimpleRequestHandler(dispatcher=dp, bot=bot).handle(request)
            app.router.add_post(f"/webhook/{quote(settings.bot.token, safe='')}", webhook_handler)
            try:
                setup_application(app, dp, bot=bot)
            except Exception as setup_err:
                sys.stderr.write(f"WARN: setup_application failed (non-fatal): {setup_err}\n")
                sys.stderr.write("DEBUG: Starting web server anyway\n")
                sys.stderr.flush()
            web.run_app(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
        else:
            sys.stderr.write("DEBUG: POLLING mode\n")
            sys.stderr.flush()
            asyncio.run(dp.start_polling(bot))
    except Exception as e:
        sys.stderr.write(f"CRITICAL: Loop fail: {e}\n")
        sys.stderr.flush()

if __name__ == "__main__":
    main()
