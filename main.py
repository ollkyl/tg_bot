import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from bot.handlers import register_handlers
from parser.parser import main_parser
from dotenv import dotenv_values
import asyncpg
from sqlalchemy.ext.asyncio import create_async_engine
from db import Base, DATABASE_URL

env_values = dotenv_values(".env")
API_TOKEN = env_values["API_TOKEN"]
ADMIN_ID = int(env_values["ADMIN_ID"])
WEBHOOK_HOST = env_values.get("WEBHOOK_HOST", "https://your-domain.com")
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(env_values.get("PORT", 8080))

DB_HOST = env_values["DB_HOST"]
DB_PORT = env_values["DB_PORT"]
DB_NAME = env_values["DB_NAME"]
DB_USER = env_values["DB_USER"]
DB_PASS = env_values["DB_PASS"]


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


async def on_startup(bot: Bot):
    await bot.set_webhook(WEBHOOK_URL)
    print(f"Webhook установлен: {WEBHOOK_URL}")


async def on_shutdown(bot: Bot):
    await bot.delete_webhook()
    print("Webhook удален")


async def main():
    await wait_for_postgres()
    await init_db()
    bot = Bot(token=API_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    register_handlers(dp, bot, ADMIN_ID)

    app = web.Application()
    webhook_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    webhook_handler.register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, WEBAPP_HOST, WEBAPP_PORT)

    await asyncio.gather(site.start(), main_parser(), on_startup(bot))
    try:
        await asyncio.Event().wait()
    finally:
        await on_shutdown(bot)
        await runner.cleanup()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
