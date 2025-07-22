import asyncio
import aiohttp
import os
from datetime import datetime, timedelta
import logging
from db import add_apartment, async_session, Apartment
from parser.sending_messages import send_apartment_notification

from sqlalchemy.sql import select, delete
import json
from bs4 import BeautifulSoup

ALGOLIA_BASE_URL = os.getenv("ALGOLIA_BASE_URL")
ALGOLIA_API_KEY = os.getenv("ALGOLIA_API_KEY")
ALGOLIA_APP_ID = os.getenv("ALGOLIA_APP_ID")
BAYUT_COOKIE = os.getenv("BAYUT_COOKIE")

ID_LIST_FILE = "id_list.txt"
LAST_CLEANUP_FILE = "last_cleanup.txt"
CLEANUP_INTERVAL_HOURS = 12
CHECK_INTERVAL_MINUTES = 10
DB_CLEANUP_DAYS = 7
print("ALGOLIA_API_KEY =", repr(ALGOLIA_API_KEY))
print("ALGOLIA_APP_ID =", repr(ALGOLIA_APP_ID))

headers = {
    "X-Algolia-API-Key": ALGOLIA_API_KEY,
    "X-Algolia-Application-Id": ALGOLIA_APP_ID,
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/138.0.0.0 Safari/537.36",
    "Referer": "https://www.bayut.com/",
    "Origin": "https://www.bayut.com",
    "Accept-Language": "ru",
}
if BAYUT_COOKIE:
    headers["Cookie"] = BAYUT_COOKIE

try:
    with open("parser/districts.json", "r", encoding="utf-8") as f:
        district_mapping = json.load(f)
except FileNotFoundError:
    logging.error("Файл districts.json не найден.")
    district_mapping = {}
except json.JSONDecodeError as e:
    logging.error(f"Некорректный JSON в districts.json: {e}.")
    district_mapping = {}

# Чтение существующих ID
existing_ids = set()
if os.path.exists(ID_LIST_FILE):
    with open(ID_LIST_FILE, "r") as f:
        existing_ids = set(line.strip() for line in f if line.strip())


async def get_contact_phone_from_html(session, external_id):
    url = f"https://www.bayut.com/property/details-{external_id}.html"
    try:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                html = await response.text()
                soup = BeautifulSoup(html, "html.parser")
                phone_elem = soup.select_one("span._95c634a6._2454d03d > a > span")
                if phone_elem:
                    return phone_elem.get_text(strip=True)
                tel_link = soup.find("a", href=lambda x: x and x.startswith("tel:"))
                if tel_link:
                    return tel_link["href"].replace("tel:", "").strip()
                logging.warning(f"Не найден телефон для external_id={external_id}")
                return "No phone found"
            logging.error(
                f"Ошибка загрузки HTML для телефона external_id={external_id}: статус {response.status}"
            )
            return "No phone found"
    except Exception as e:
        logging.error(f"Ошибка получения телефона для external_id={external_id}: {e}")
        return "No phone"


def find_district(district_name):
    for district, areas in district_mapping.items():
        if district_name in areas:
            return district
    return district_name


async def cleanup_old_ids_and_db():
    current_time = datetime.now()
    if os.path.exists(LAST_CLEANUP_FILE):
        with open(LAST_CLEANUP_FILE, "r") as f:
            content = f.read().strip()
            last_cleanup = datetime.fromtimestamp(float(content)) if content else current_time
        if (current_time - last_cleanup).total_seconds() >= CLEANUP_INTERVAL_HOURS * 3600:
            with open(ID_LIST_FILE, "w") as f:
                f.write("")
            async with async_session() as db_session:
                async with db_session.begin():
                    await db_session.execute(
                        delete(Apartment).where(
                            Apartment.created_at < current_time - timedelta(days=DB_CLEANUP_DAYS)
                        )
                    )
                    await db_session.commit()
            with open(LAST_CLEANUP_FILE, "w") as f:
                f.write(str(current_time.timestamp()))
            logging.info("Очищены id_list.txt и старые записи в БД")


async def fetch_hits(session, page):
    start_time = datetime.now() - timedelta(minutes=12)
    start_timestamp = int(start_time.timestamp())
    data = {
        "requests": [
            {
                "indexName": "bayut-production-ads-en",
                "params": f"hitsPerPage=1000&page={page}&filters=purpose:for-rent&numericFilters=createdAt>{start_timestamp}",
            }
        ]
    }
    try:
        async with session.post(
            "https://ll8iz711cs-dsn.algolia.net/1/indexes/*/queries", headers=headers, json=data
        ) as response:
            if response.status == 200:
                return await response.json()
            logging.error(f"Ошибка Algolia API для page={page}: статус {response.status}")
            return {"results": [{"hits": []}]}
    except Exception as e:
        logging.error(f"Ошибка запроса Algolia API: {e}")
        return {"results": [{"hits": []}]}


async def fetch_detail(session, object_id):
    detail_url = f"{ALGOLIA_BASE_URL}/{object_id}"
    try:
        async with session.get(detail_url, headers=headers) as response:
            if response.status == 200:
                return await response.json()
            logging.error(f"Ошибка Algolia API для object_id={object_id}: статус {response.status}")
            return None
    except Exception as e:
        logging.error(f"Ошибка запроса Algolia API для object_id={object_id}: {e}")
        return None


async def process_new_ads():
    await cleanup_old_ids_and_db()
    stats = {"successful_adds": 0}
    async with aiohttp.ClientSession() as session:
        try:
            all_hits = []
            page = 0
            while True:
                result = await fetch_hits(session, page)
                hits = result["results"][0]["hits"]
                if not hits:
                    break
                all_hits.extend(hits)
                page += 1
                await asyncio.sleep(1)

            new_hits = [hit for hit in all_hits if hit["externalID"] not in existing_ids]
            logging.info(f"Найдено новых объявлений: {len(new_hits)}")

            async with async_session() as db_session:
                async with db_session.begin():
                    for hit in new_hits:
                        # Проверка категории
                        external_id = hit["externalID"]
                        object_id = hit.get("objectID")
                        created_at = datetime.fromtimestamp(hit.get("createdAt", 0)).strftime(
                            "%H:%M"
                        )
                        if any(
                            cat["name"].lower() in ["office", "offices", "commercial"]
                            for cat in hit.get("category", [])
                        ):
                            logging.info(
                                f"Пропуск: externalID={external_id}, категория {hit.get('category', [])}"
                            )
                            continue
                        logging.info(
                            f"Обработка: externalID={external_id}, objectID={object_id}, createdAt={created_at}"
                        )

                        existing_apartment = await db_session.execute(
                            select(Apartment).where(Apartment.object_id == object_id)
                        )
                        if existing_apartment.scalars().first():
                            logging.info(
                                f"Пропуск: объявление с objectID={object_id} уже существует"
                            )
                            continue

                        detail_hit = await fetch_detail(session, object_id)
                        if detail_hit:
                            owner = await get_contact_phone_from_html(session, external_id)
                            if owner == "No phone found":
                                owner = detail_hit.get("phoneNumber", {}).get("mobile", "Unknown")
                            name = detail_hit.get("title", "No title")
                            price = detail_hit.get("price", 0.0)

                            rooms_raw = detail_hit.get("rooms")
                            if rooms_raw in [None, 0]:
                                rooms = "100"
                            else:
                                rooms = str(rooms_raw)
                            location_data = detail_hit.get("location", [])
                            district_area = next(
                                (
                                    loc["name"]
                                    for loc in location_data
                                    if loc.get("type") == "neighbourhood"
                                ),
                                "Unknown",
                            )
                            district = find_district(district_area)
                            raw_period = detail_hit.get("rentFrequency", "yearly")
                            period = raw_period
                            # Пересчёт цены в месяц
                            if raw_period == "yearly":
                                price = round(price / 12)
                            elif raw_period == "weekly":
                                price = round(price * 4.345)  # недель → месяц
                            elif raw_period == "daily":
                                price = round(price * 30)

                            furnishing_status = detail_hit.get("furnishingStatus")
                            if furnishing_status == "furnished":
                                furnishing = True
                            elif furnishing_status == "unfurnished":
                                furnishing = False
                            else:
                                furnishing = None

                            amenities = detail_hit.get("amenities_l3", [])
                            info = ", ".join(amenities) if amenities else "Нет удобств"

                            logging.info(f"Удобства для {external_id}: {info}")

                            cover_id = detail_hit.get("coverPhoto", {}).get("externalID", "")
                            photo_ids = [
                                str(photo_id) for photo_id in detail_hit.get("photoIDs", [])
                            ]
                            if cover_id and str(cover_id) not in photo_ids:
                                photo_ids.insert(0, str(cover_id))
                            link = f"https://www.bayut.com/property/details-{external_id}.html"

                            apartment_id, matching_clients = await add_apartment(
                                owner,
                                name,
                                price,
                                rooms,
                                district,
                                period,
                                furnishing,
                                info,
                                photo_ids,
                                object_id,
                                link,
                            )
                            logging.info(
                                f"Сохранено в БД: ID={apartment_id}, Клиентов: {len(matching_clients)}, Link={link}"
                            )
                            stats["successful_adds"] += 1

                            await send_apartment_notification(apartment_id)
                        else:
                            logging.error(f"Ошибка API для external_id={external_id}: нет данных")
                        await asyncio.sleep(20)
        finally:
            await session.close()

    if new_hits:
        with open(ID_LIST_FILE, "a") as f:
            for hit in new_hits:
                f.write(f"{hit['externalID']}\n")
        logging.info(f"Добавлено новых ID в id_list.txt: {len(new_hits)}")


async def main_parser():
    while True:
        await process_new_ads()
        await asyncio.sleep(CHECK_INTERVAL_MINUTES * 60)


if __name__ == "__main__":
    asyncio.run(main_parser())
