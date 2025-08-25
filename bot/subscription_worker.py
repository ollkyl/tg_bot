import asyncio
from db import create_database_engine_and_session, Subscription
from datetime import datetime
from sqlalchemy import select
from aiogram import Bot
import logging
import os

# Global database engine and session for this thread
db_engine = None
async_session = None
bot = None


async def init_worker_db():
    """Initialize database engine and session for worker thread."""
    global db_engine, async_session
    db_engine, async_session = create_database_engine_and_session()


async def init_worker_bot():
    """Initialize bot for worker thread."""
    global bot
    bot = Bot(token=os.getenv("API_TOKEN"))


async def subscription_expiration_worker():
    # Initialize database and bot for this thread
    await init_worker_db()
    await init_worker_bot()

    while True:
        print("subscription_expiration_worker")
        async with async_session() as session:
            now = datetime.utcnow()
            result = await session.execute(
                select(Subscription).where(
                    Subscription.status == "active", Subscription.end_date < now
                )
            )
            expired = result.scalars().all()
            for sub in expired:
                sub.status = "expired"
                try:
                    await bot.send_message(
                        chat_id=sub.user_id,
                        text="❗ Ваша подписка истекла. Чтобы продолжить получать объявления, оформите новую.",
                    )
                except Exception as e:
                    logging.error(f"Ошибка отправки уведомления {sub.user_id}: {e}")
            await session.commit()
        await asyncio.sleep(800)
