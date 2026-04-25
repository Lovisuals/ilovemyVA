import asyncio
from aiogram import BaseMiddleware, Dispatcher
from aiogram.types import Update

class M1(BaseMiddleware):
    async def __call__(self, handler, event, data):
        print("M1 BEFORE")
        await handler(event, data)
        print("M1 AFTER")

class M2(BaseMiddleware):
    async def __call__(self, handler, event, data):
        print("M2 BEFORE")
        await handler(event, data)
        print("M2 AFTER")

async def main():
    dp = Dispatcher()
    dp.update.outer_middleware(M1())
    dp.update.outer_middleware(M2())
    
    async def dummy_handler(event, data):
        print("HANDLER")
        
    class DummyUpdate:
        pass
        
    try:
        await dp.update.middleware.wrap_middlewares(dp.update.handlers, dummy_handler)(DummyUpdate(), {})
    except Exception as e:
        print(e)

asyncio.run(main())
