from aiogram import Dispatcher
import asyncio
async def test():
    dp = Dispatcher()
    try:
        dp["test"] = "value"
        print(f"Success: {dp['test']}")
    except Exception as e:
        print(f"Failed: {e}")
if __name__ == "__main__":
    asyncio.run(test())
