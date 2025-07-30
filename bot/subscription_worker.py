import asyncio
from db import async_session, Subscription
from datetime import datetime
from sqlalchemy import select
from aiogram import Bot
import logging
import os

bot = Bot(token=os.getenv("API_TOKEN"))


async def subscription_expiration_worker():
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
