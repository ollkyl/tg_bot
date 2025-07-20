from aiogram import Bot
from aiogram.utils.media_group import MediaGroupBuilder
import logging
import asyncio
import aiohttp
from db import async_session, Apartment, find_matching_clients
from dotenv import dotenv_values
from sqlalchemy.sql import select


# Инициализация бота
env_values = dotenv_values(".env")
bot = Bot(token=env_values.get("API_TOKEN"))


async def is_url_accessible(url: str) -> bool:
    async with aiohttp.ClientSession() as session:
        try:
            async with session.head(url, timeout=5) as response:
                return response.status == 200
        except Exception:
            return False


def get_photo_urls(photo_ids: list[str], limit: int = 10) -> list[str]:
    return [f"https://images.bayut.com/thumbnails/{pid}-1066x800.webp" for pid in photo_ids[:limit]]


async def send_media_group(
    chat_id: str, photo_urls: list[str], message: str, max_attempts: int = 5
):
    valid_photo_urls = [url for url in photo_urls if await is_url_accessible(url)]
    if not valid_photo_urls:
        logging.error(f"[NOTIFY] Нет доступных фото для отправки в {chat_id}")
        return False

    for attempt in range(max_attempts):
        try:
            media_group = MediaGroupBuilder(caption=message)
            for url in valid_photo_urls:
                media_group.add_photo(media=url, parse_mode="HTML")
            await bot.send_media_group(chat_id=chat_id, media=media_group.build())
            return True
        except Exception as e:
            if "Too Many Requests" in str(e):
                retry_after = (
                    int(str(e).split("retry after ")[-1].split()[0]) + 1
                    if "retry after" in str(e)
                    else 30
                )
                await asyncio.sleep(retry_after)
            elif "WEBPAGE_CURL_FAILED" in str(e) or "WEBPAGE_MEDIA_EMPTY" in str(e):
                await asyncio.sleep(10)
            else:
                logging.error(f"[NOTIFY] Ошибка отправки в {chat_id} (попытка {attempt + 1}): {e}")
                return False
        await asyncio.sleep(1)
    return False


async def send_apartment_notification(apartment_id):
    async with async_session() as session:
        apt = (
            (await session.execute(select(Apartment).where(Apartment.id == apartment_id)))
            .scalars()
            .first()
        )
        if not apt:
            logging.error(f"[NOTIFY] Квартира с ID {apartment_id} не найдена")
            return

        furnishing_translations = {
            "furnished": "Меблированная",
            "unfurnished": "Немеблированная",
        }
        furnishing = furnishing_translations.get(apt.furnishing, apt.furnishing or "Не указано")
        name = apt.name
        price = apt.price
        rooms = apt.rooms
        if rooms == 100 or rooms == "100":
            rooms = "студия"
        district = apt.district
        period = apt.period
        if period == "monthly":
            period = "помесячно"
        elif period == "daily":
            period = "посуточно"
        elif period == "yearly":
            period = "от года"
        else:
            period = "Не указано"
        furnishing = furnishing
        info = apt.info or "Не указаны удобства"
        link = apt.link
        owner = apt.owner.replace(" ", "_")

        message = (
            f"🏠 {name}\n"
            f"💰 Цена в месяц: {price} AED\n"
            f"🛏️ Комнаты: {rooms}\n"
            f"📍 Район: {district}\n"
            f"⌛ Период: {period}\n"
            f"🪑 {furnishing}\n"
            f"ℹ️ Удобства: {info}\n"
            f"🔗 <a href='{link}'>Ссылка на объявление</a>\n"
            f"📞 {owner}"
        )

        channel_id = "@apartDubaiApart"
        photo_urls = get_photo_urls(apt.photo_ids)

        # Отправка в канал
        if await send_media_group(channel_id, photo_urls, message):
            logging.info(f"[NOTIFY] Отправлено в канал для apartment_id={apartment_id}")

        # Отправка клиентам
        matching_clients = await find_matching_clients(apt)
        if matching_clients:
            sent_usernames = []
            for user_id, user_name in matching_clients:
                if not user_id:
                    continue
                if await send_media_group(user_id, photo_urls, message):
                    sent_usernames.append(user_name or "Без имени")
            if sent_usernames:
                try:
                    await bot.send_message(
                        chat_id=channel_id,
                        text=f"Сообщения отправлены: {', '.join(sent_usernames)}",
                        parse_mode="HTML",
                    )
                    logging.info(
                        f"[NOTIFY] Отправлен список клиентов для apartment_id={apartment_id}"
                    )
                except Exception as e:
                    logging.error(f"[NOTIFY] Ошибка отправки списка клиентов: {e}")
        else:
            logging.info(f"[NOTIFY] Нет клиентов для apartment_id={apartment_id}")
