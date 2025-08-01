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
            logging.info("✅ PostgreSQL доступен!")
            return
        except Exception as e:
            logging.error(f"⏳ Ожидание PostgreSQL: {e}")
            await asyncio.sleep(2)


async def init_db():
    engine = create_async_engine(DATABASE_URL, echo=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()


async def on_startup(bot: Bot):
    await bot.set_webhook(WEBHOOK_URL)
    logging.info(f"Webhook установлен: {WEBHOOK_URL}")


async def on_shutdown(bot: Bot):
    await bot.delete_webhook()
    logging.info("Webhook удален")


async def main():
    logging.basicConfig(level=logging.INFO)
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

        # Запускаем парсер и воркер как фоновые задачи
        asyncio.create_task(main_parser())
        asyncio.create_task(subscription_expiration_worker())

        try:
            await asyncio.Event().wait()  # Основной цикл для webhook
        finally:
            await on_shutdown(bot)
            await runner.cleanup()

    else:
        await bot.delete_webhook()
        logging.info("Webhook удалён для запуска polling")
        logging.info("Запуск в режиме polling, для локальной разработки")
        try:
            # Запускаем polling в основном цикле для приоритета
            await asyncio.gather(
                dp.start_polling(bot),  # Бот в приоритете
                background_task(main_parser),  # Парсер с задержкой
                background_task(subscription_expiration_worker),  # Воркер с задержкой
            )
        except Exception as e:
            logging.error(f"Ошибка в polling или задачах: {e}")
        finally:
            await bot.session.close()


async def background_task(coro):
    """Обёртка для фоновых задач с меньшим приоритетом"""
    await asyncio.sleep(1)  # Даём боту запуститься первым
    try:
        await coro()
    except Exception as e:
        logging.error(f"Ошибка в фоновой задаче {coro.__name__}: {e}")


if __name__ == "__main__":
    asyncio.run(main())
