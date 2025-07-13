from aiogram import Bot
from aiogram.types import InputMediaPhoto
from aiogram.utils.media_group import MediaGroupBuilder
import logging
import asyncio
import aiohttp
from db import async_session, Apartment, find_matching_clients
from dotenv import dotenv_values
from sqlalchemy.sql import select

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Инициализация бота
env_values = dotenv_values(".env")
BOT_TOKEN = env_values.get("API_TOKEN")
bot = Bot(token=BOT_TOKEN)


async def is_url_accessible(url: str) -> bool:
    async with aiohttp.ClientSession() as session:
        try:
            async with session.head(url, timeout=5) as response:
                return response.status == 200
        except Exception:
            return False


def get_photo_urls(photo_ids: list[str], limit: int = 10) -> list[str]:
    return [f"https://images.bayut.com/thumbnails/{pid}-1066x800.webp" for pid in photo_ids[:limit]]


async def send_apartment_notification(apartment_id):
    async with async_session() as session:
        result = await session.execute(select(Apartment).where(Apartment.id == apartment_id))
        apt = result.scalars().first()
        if not apt:
            logging.error(f"[NOTIFY] Квартира с ID {apartment_id} не найдена")
            return

        photo_urls = get_photo_urls(apt.photo_ids)
        # Фильтруем только доступные URL-ы
        valid_photo_urls = []
        for url in photo_urls:
            if await is_url_accessible(url):
                valid_photo_urls.append(url)
        if not valid_photo_urls:
            logging.error(f"[NOTIFY] Нет доступных фото для apartment_id={apartment_id}")
            return

        message = (
            f"🏠 {apt.name}\n"
            f"💰 Цена: {apt.price} AED\n"
            f"🛏️ Комнаты: {apt.rooms}\n"
            f"📍 Район: {apt.district}\n"
            f"⌛ Период: {apt.period}\n"
            f"ℹ️ Инфо: {apt.info or 'Нет описания'}\n"
            f"🔗 <a href='{apt.link}'>Ссылка на объявление</a>\n"
            f"📞 @{apt.owner.replace(' ', '_')}"
        )

        channel_id = "@apartDubaiApart"
        max_attempts = 5
        for attempt in range(max_attempts):
            try:
                media_group = MediaGroupBuilder(caption=message)
                for url in valid_photo_urls:
                    media_group.add_photo(media=url, parse_mode="HTML")
                await bot.send_media_group(chat_id=channel_id, media=media_group.build())
                logging.info(f"[NOTIFY] Успешно отправлено в канал для apartment_id={apartment_id}")
                break
            except Exception as e:
                if "Too Many Requests" in str(e):
                    try:
                        retry_after = int(str(e).split("retry after ")[-1].split()[0]) + 1
                    except (IndexError, ValueError):
                        retry_after = 30
                    logging.warning(
                        f"[NOTIFY] Flood control в канал, retry after {retry_after}s, attempt {attempt + 1}/{max_attempts}"
                    )
                    await asyncio.sleep(retry_after)
                elif "WEBPAGE_CURL_FAILED" in str(e) or "WEBPAGE_MEDIA_EMPTY" in str(e):
                    logging.warning(
                        f"[NOTIFY] WEBPAGE_CURL_FAILED или WEBPAGE_MEDIA_EMPTY в канал, retry after 10s, attempt {attempt + 1}/{max_attempts}"
                    )
                    await asyncio.sleep(10)
                else:
                    logging.error(f"[NOTIFY] Ошибка в канал (попытка {attempt + 1}): {e}")
                    break
            await asyncio.sleep(1)

        # Отправка клиентам
        matching_clients = await find_matching_clients(apt)
        if matching_clients:
            sent_usernames = []
            for user_id, user_name in matching_clients:
                if not user_id:
                    continue
                for attempt in range(max_attempts):
                    try:
                        media_group = MediaGroupBuilder(caption=message)
                        for url in valid_photo_urls:
                            media_group.add_photo(media=url, parse_mode="HTML")
                        await bot.send_media_group(chat_id=user_id, media=media_group.build())
                        sent_usernames.append(user_name or "Без имени")
                        logging.info(
                            f"[NOTIFY] Успешно отправлено пользователю {user_id} для apartment_id={apartment_id}"
                        )
                        break
                    except Exception as e:
                        if "Too Many Requests" in str(e):
                            try:
                                retry_after = int(str(e).split("retry after ")[-1].split()[0]) + 1
                            except (IndexError, ValueError):
                                retry_after = 30
                            logging.warning(
                                f"[NOTIFY] Flood control для {user_id}, retry after {retry_after}s, attempt {attempt + 1}/{max_attempts}"
                            )
                            await asyncio.sleep(retry_after)
                        elif "WEBPAGE_CURL_FAILED" in str(e) or "WEBPAGE_MEDIA_EMPTY" in str(e):
                            logging.warning(
                                f"[NOTIFY] WEBPAGE_CURL_FAILED или WEBPAGE_MEDIA_EMPTY для {user_id}, retry after 10s, attempt {attempt + 1}/{max_attempts}"
                            )
                            await asyncio.sleep(10)
                        else:
                            logging.error(
                                f"[NOTIFY] Не отправилось {user_id} (попытка {attempt + 1}): {e}"
                            )
                            break
                    await asyncio.sleep(1)
            if sent_usernames:
                try:
                    await bot.send_message(
                        chat_id=channel_id,
                        text=f"Сообщения отправлены: {', '.join(sent_usernames)}",
                        parse_mode="HTML",
                    )
                    logging.info(
                        f"[NOTIFY] Успешно отправлен список клиентов для apartment_id={apartment_id}"
                    )
                except Exception as e:
                    logging.error(f"[NOTIFY] Ошибка отправки списка клиентов: {e}")
        else:
            logging.info(f"[NOTIFY] Нет клиентов для apartment_id={apartment_id}")
