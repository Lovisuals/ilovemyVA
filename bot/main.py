"bot/main.py"

import logging
from aiohttp import web

from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from bot.config import settings
from bot.strings import BOT_ONLINE, BOT_SHUTDOWN
from bot.routers import (
    admin, buckets, drafting, editing, scheduling, 
    broadcast, moderation, settings as settings_router, 
    onboarding, user_management
)
from bot.middlewares.auth import AuthMiddleware
from bot.middlewares.rate_limit import RateLimitMiddleware
from bot.middlewares.logging_mw import LoggingMiddleware
from bot.middlewares.error_handler import ErrorHandlerMiddleware
from bot.scheduler.setup import setup_scheduler

async def on_startup(bot: Bot):
    await bot.set_webhook(
        url=f"{settings.bot.webhook_url}/webhook/{settings.bot.token}",
        drop_pending_updates=True
    )
    await bot.send_message(settings.bot.owner_id, BOT_ONLINE)

async def on_shutdown(bot: Bot):
    await bot.send_message(settings.bot.owner_id, BOT_SHUTDOWN)
    await bot.delete_webhook()

async def health_check(request):
    return web.json_response({"status": "ok", "version": "1.3"})

def main():
    bot = Bot(token=settings.bot.token)
    dp = Dispatcher()

    dp.include_routers(
        admin.router, buckets.router, drafting.router, 
        editing.router, scheduling.router, broadcast.router, 
        moderation.router, settings_router.router, 
        onboarding.router, user_management.router
    )

    dp.update.outer_middleware(LoggingMiddleware())
    dp.update.outer_middleware(RateLimitMiddleware())
    dp.update.outer_middleware(AuthMiddleware())
    dp.update.outer_middleware(ErrorHandlerMiddleware())

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    scheduler = setup_scheduler()
    scheduler.start()

    app = web.Application()
    app.router.add_get("/health", health_check)
    
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot
    )
    webhook_requests_handler.register(app, path=f"/webhook/{settings.bot.token}")

    setup_application(app, dp, bot=bot)
    web.run_app(app, host="0.0.0.0", port=settings.bot.port)

if __name__ == "__main__":
    main()
