import asyncio
import logging
from aiogram import Bot, Dispatcher, types
import handlers

logging.basicConfig(level=logging.INFO)
bot = Bot(token="7487870032:AAGqvwbK9xB91cMM9YriPEGHkdHiuW6u9bw")
dp = Dispatcher()

dp.include_routers(handlers.router)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
