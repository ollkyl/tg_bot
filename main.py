import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from bot.handlers import register_handlers
from parser.parser import main_parser
from sqlalchemy.ext.asyncio import create_async_engine
from db import Base, DATABASE_URL
from dotenv import load_dotenv
from pathlib import Path
from bot.subscription_worker import subscription_expiration_worker


load_dotenv(dotenv_path=Path(".") / ".env")

API_TOKEN = os.environ["API_TOKEN"]
ADMIN_ID = int(os.environ["ADMIN_ID"])
WEBHOOK_HOST = os.environ.get("WEBHOOK_HOST")
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.environ.get("PORT", 8080))

DB_HOST = os.environ["DB_HOST"]
DB_PORT = os.environ["DB_PORT"]
DB_NAME = os.environ["DB_NAME"]
DB_USER = os.environ["DB_USER"]
DB_PASS = os.environ["DB_PASS"]


async def wait_for_postgres():
    import asyncpg

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

    use_webhook = os.environ.get("USE_WEBHOOK", "False").lower() == "true"

    if use_webhook:
        app = web.Application()
        webhook_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
        webhook_handler.register(app, path=WEBHOOK_PATH)
        setup_application(app, dp, bot=bot)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, WEBAPP_HOST, WEBAPP_PORT)

        await site.start()
        await on_startup(bot)
        asyncio.create_task(main_parser())
        asyncio.create_task(subscription_expiration_worker())  # 🔥 Воркер по подписке

        try:
            await asyncio.Event().wait()
        finally:
            await on_shutdown(bot)
            await runner.cleanup()

    else:
        print("Запуск в режиме polling, для локальной разработки")
        try:
            await asyncio.gather(
                dp.start_polling(bot),
                main_parser(),
                subscription_expiration_worker(),  # 🔥 Воркер по подписке
            )
        except Exception as e:
            print(f"Ошибка в polling или парсере: {e}")
        finally:
            await bot.session.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
