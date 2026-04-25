import asyncio
from aiogram import Bot, Dispatcher, BaseMiddleware
from aiogram.types import Update

class MW(BaseMiddleware):
    async def __call__(self, h, e, d):
        print(f"BOT IN DATA: {d.get('bot')}")
        return await h(e, d)

async def main():
    bot = Bot(token="1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    dp = Dispatcher()
    dp.update.outer_middleware(MW())
    
    # Mocking feed_update logic
    update = Update(update_id=1)
    await dp.feed_update(bot, update)

if __name__ == "__main__":
    asyncio.run(main())
