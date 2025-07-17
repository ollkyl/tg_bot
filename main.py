import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from bot.handlers import register_handlers
from parser.parser import main_parser
from dotenv import dotenv_values

logging.basicConfig(level=logging.INFO, filename="app.log")
logger = logging.getLogger(__name__)

env_values = dotenv_values(".env")
API_TOKEN = env_values["API_TOKEN"]
ADMIN_ID = int(env_values["ADMIN_ID"])


async def main():
    bot = Bot(token=API_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    register_handlers(dp, bot, ADMIN_ID)
    await asyncio.gather(dp.start_polling(bot), main_parser())


if __name__ == "__main__":
    asyncio.run(main())
