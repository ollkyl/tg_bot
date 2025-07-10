from aiogram import Bot
from aiogram.types import InputMediaPhoto, InputMediaVideo
import logging
from db import async_session, Apartment
import requests
from dotenv import dotenv_values
from db import find_matching_clients

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота
env_values = dotenv_values(".env")
BOT_TOKEN = env_values.get("API_TOKEN")
bot = Bot(token=BOT_TOKEN)

# Заголовки для запроса к Algolia
ALGOLIA_API_KEY = env_values.get("ALGOLIA_API_KEY")
ALGOLIA_APP_ID = env_values.get("ALGOLIA_APP_ID")
headers = {
    "X-Algolia-API-Key": ALGOLIA_API_KEY,
    "X-Algolia-Application-Id": ALGOLIA_APP_ID,
    "Content-Type": "application/json",
}


async def get_photo_url(object_id):
    """Получает URL фото по object_id из Algolia."""
    if not object_id:
        return None
    detail_url = f"https://LL8IZ711CS-dsn.algolia.net/1/indexes/bayut-production-ads-en/{object_id}"
    try:
        response = requests.get(detail_url, headers=headers, timeout=10)
        if response.status_code == 200:
            detail_hit = response.json()
            return detail_hit.get("coverPhoto", {}).get("url")
        else:
            logging.error(f"Ошибка API для object_id {object_id}: {response.status_code}")
            return None
    except Exception as e:
        logging.error(f"Ошибка при запросе URL фото: {e}")
        return None


async def send_apartment_notification(apartment_id):
    """Отправляет уведомления о новой квартире из БД."""
    async with async_session() as session:
        result = await session.execute(select(Apartment).where(Apartment.id == apartment_id))
        apt = result.scalars().first()
        if not apt:
            logging.error(f"Квартира с ID {apartment_id} не найдена.")
            return

        # Получаем URL фото
        photo_url = await get_photo_url(apt.object_id)

        # Формируем сообщение
        message = (
            f"🏠 {apt.name}\n"
            f"💰 Цена: {apt.price} AED\n"
            f"🛏️ Комнаты: {apt.rooms}\n"
            f"📍 Район: {apt.district}\n"
            f"⌛ Период: {apt.period}\n"
            f"ℹ️ Инфо: {apt.info or 'Нет описания'}\n"
            f"Контакт: @{apt.owner.replace(' ', '_')}"
        )

        # Отправка в канал
        channel_id = "@apartDubaiApart"
        try:
            if photo_url:
                await bot.send_photo(chat_id=channel_id, photo=photo_url, caption=message)
            else:
                await bot.send_message(chat_id=channel_id, text=message)
        except Exception as e:
            logging.error(f"Ошибка отправки в канал: {e}")

        # Поиск совпадений с клиентами
        matching_clients = await find_matching_clients(apt)
        if matching_clients:
            sent_usernames = []
            for user_id, user_name in matching_clients:
                try:
                    if user_id is not None:
                        if user_name:
                            sent_usernames.append(user_name)
                        else:
                            sent_usernames.append("Без имени")
                        if photo_url:
                            await bot.send_photo(chat_id=user_id, photo=photo_url, caption=message)
                        else:
                            await bot.send_message(chat_id=user_id, text=message)
                except Exception as e:
                    logging.error(f"Не удалось отправить сообщение пользователю {user_id}: {e}")
            if sent_usernames:
                await bot.send_message(
                    chat_id=channel_id, text=f"Сообщения отправлены: {', '.join(sent_usernames)}"
                )
        else:
            logging.info("Подходящих клиентов не найдено.")
