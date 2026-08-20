import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

import database as db
from handlers import common, expenses, tasks
from scheduler import setup_scheduler

logging.basicConfig(level=logging.INFO)


BOT_TOKEN = os.getenv("BOT_TOKEN", "8595719345:AAERYooeaLSJ0uKzS_rvd9Y-0T0s_dO94dM")


async def main():
    if BOT_TOKEN == "ВСТАВЬ_СЮДА_ТВОЙ_ТОКЕН":
        print("⚠️  Не забудь вставить токен бота в bot.py или задать переменную окружения BOT_TOKEN")
        return

    await db.init_db()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(common.router)
    dp.include_router(tasks.router)
    dp.include_router(expenses.router)

    scheduler = setup_scheduler(bot)
    scheduler.start()

    print("Бот запущен ✅")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())