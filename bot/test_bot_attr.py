from aiogram import Bot
import asyncio
async def test():
    bot = Bot(token="123:abc")
    try:
        bot["test"] = "value"
        print(f"Success: {bot['test']}")
    except Exception as e:
        print(f"Failed: {e}")
    await bot.session.close()
if __name__ == "__main__":
    asyncio.run(test())
