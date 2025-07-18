import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from bot.handlers import register_handlers
from parser.parser import main_parser
import asyncpg
from sqlalchemy.ext.asyncio import create_async_engine
from db import Base, DATABASE_URL
import os

API_TOKEN = os.getenv("API_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")


# Ожидание запуска PostgreSQL
async def wait_for_postgres():
    while True:
        try:
            conn = await asyncpg.connect(
                user=DB_USER, password=DB_PASS, database=DB_NAME, host=DB_HOST, port=int(DB_PORT)
            )
            await conn.close()
            print("✅ PostgreSQL доступен!")
            return
        except Exception as e:
            print(f"⏳ Ожидание PostgreSQL: {e}")
            await asyncio.sleep(2)


async def init_db():
    engine = create_async_engine(DATABASE_URL, echo=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()


async def main():
    await wait_for_postgres()
    await init_db()
    bot = Bot(token=API_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    register_handlers(dp, bot, ADMIN_ID)
    await asyncio.gather(dp.start_polling(bot), main_parser())


if __name__ == "__main__":
    asyncio.run(main())
