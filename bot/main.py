import logging
import os
import secrets
from urllib.parse import quote
from aiohttp import web

from aiogram import Bot, Dispatcher
from aiogram.types import Update
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

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

WEBHOOK_SECRET = secrets.token_hex(32)

async def on_startup(bot: Bot, dispatcher: Dispatcher, app: web.Application):
    await bot.set_webhook(
        url=f"{settings.bot.webhook_url}/webhook/{quote(settings.bot.token, safe='')}",
        secret_token=WEBHOOK_SECRET,
        drop_pending_updates=True,
        allowed_updates=["message", "callback_query", "channel_post"]
    )

    scheduler = await setup_scheduler()
    app["scheduler"] = scheduler
    await scheduler.start_in_background()

    await bot.send_message(settings.bot.owner_id, BOT_ONLINE)

async def on_shutdown(bot: Bot, dispatcher: Dispatcher, app: web.Application):
    await bot.send_message(settings.bot.owner_id, BOT_SHUTDOWN)

    scheduler = app.get("scheduler")
    if scheduler:
        await scheduler.stop()

    await bot.delete_webhook()

async def health_check(request):
    return web.json_response({"status": "ok", "version": "1.3"})

def main():
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

    app = web.Application()
    app.router.add_get("/health", health_check)

    async def webhook_handler(request: web.Request) -> web.Response:
        if request.headers.get("X-Telegram-Bot-Api-Secret-Token") != WEBHOOK_SECRET:
            return web.Response(status=403)
        return await SimpleRequestHandler(dispatcher=dp, bot=bot).handle(request)

    app.router.add_post(f"/webhook/{quote(settings.bot.token, safe='')}", webhook_handler)

    setup_application(app, dp, bot=bot)
    web.run_app(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

if __name__ == "__main__":
    main()
