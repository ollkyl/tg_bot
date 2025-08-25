import asyncio
import logging
import os
import threading
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
from bot.handlers import init_main_db

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


def run_parser_in_thread():
    """Run parser in its own thread with independent event loop."""
    parser_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(parser_loop)
    parser_loop.run_until_complete(main_parser())


def run_worker_in_thread():
    """Run worker in its own thread with independent event loop."""
    worker_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(worker_loop)
    worker_loop.run_until_complete(subscription_expiration_worker())


async def main():
    logging.basicConfig(level=logging.INFO)
    await wait_for_postgres()
    await init_db()
    await init_main_db()  # Initialize database for main thread

    # Start parser in separate thread
    parser_thread = threading.Thread(target=run_parser_in_thread, name="ParserThread", daemon=True)
    parser_thread.start()
    logging.info("Запущен поток ParserThread")

    # Start worker in separate thread
    worker_thread = threading.Thread(target=run_worker_in_thread, name="WorkerThread", daemon=True)
    worker_thread.start()
    logging.info("Запущен поток WorkerThread")

    # Bot runs in main thread
    bot = Bot(token=API_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    register_handlers(dp, bot, ADMIN_ID)

    use_webhook = os.environ.get("USE_WEBHOOK", "False").lower() == "true"

    if use_webhook:
        app = web.Application()
        webhook_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
        webhook_handler.register(app, path=WEBHOOK_PATH)

        async def root(request):
            return web.json_response({"status": "ok"})

        app.router.add_route("GET", "/", root)
        app.router.add_route("HEAD", "/", root)

        setup_application(app, dp, bot=bot)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, WEBAPP_HOST, WEBAPP_PORT)
        await site.start()
        await on_startup(bot)

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
            await dp.start_polling(bot)  # бот крутится в основном потоке
        except Exception as e:
            logging.error(f"Ошибка в polling: {e}")
        finally:
            await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
