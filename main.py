from aiogram import Bot, Dispatcher
import asyncio
import logging
from dotenv import dotenv_values
from handlers import register_handlers
from db import engine, Base

logging.basicConfig(level=logging.INFO)

env_values = dotenv_values(".env")
print("env_values:", env_values)  # Для отладки
API_TOKEN = env_values.get("API_TOKEN")
ADMIN_ID = int(env_values.get("ADMIN_ID") or 0)
if API_TOKEN is None:
    raise ValueError("API_TOKEN не найден в файле .env")

bot = Bot(token=API_TOKEN)
dp = Dispatcher()


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def main():
    await init_db()  # Создаем таблицы в базе данных
    register_handlers(dp, bot, ADMIN_ID)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
