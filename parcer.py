import asyncio
import aiohttp
import os
import time
import re
from datetime import datetime, timedelta
from db import add_apartment, async_session, Apartment
from sending_messages import send_apartment_notification
from dotenv import dotenv_values
from sqlalchemy.sql import select
import json
from bs4 import BeautifulSoup

# Загрузка переменных окружения
env_values = dotenv_values(".env")
ALGOLIA_BASE_URL = env_values.get("ALGOLIA_BASE_URL")
ALGOLIA_API_KEY = env_values.get("ALGOLIA_API_KEY")
ALGOLIA_APP_ID = env_values.get("ALGOLIA_APP_ID")
BAYUT_COOKIE = env_values.get("BAYUT_COOKIE")  # Добавляем куки

# Файлы для хранения
ID_LIST_FILE = "id_list.txt"
CLEANUP_FILE = "cleanup_time.txt"
LOG_FILE = "new_ads.log"
CLEANUP_INTERVAL_HOURS = 12

# Загрузка district_mapping
try:
    with open("districts.json", "r", encoding="utf-8") as f:
        district_mapping = json.load(f)
except FileNotFoundError:
    print("Ошибка: Файл districts.json не найден.")
    district_mapping = {}
except json.JSONDecodeError as e:
    print(f"Ошибка: Некорректный JSON в districts.json: {e}.")
    district_mapping = {}

# Заголовки для запросов
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


async def get_info(session, external_id):
    url = f"https://www.bayut.com/property/details-{external_id}.html"
    try:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                html = await response.text()
                soup = BeautifulSoup(html, "html.parser")
                desc_block = soup.find("div", class_="_0a5f69b8")  # Проверь актуальный класс
                if desc_block:
                    description = desc_block.get_text(strip=True)
                    description = re.sub(r"\s+", " ", description).strip()[:500]
                    return description
                print(f"HTML: Не найдено описание для external_id={external_id}")
                return "No description found"
            print(f"Ошибка загрузки HTML страницы {external_id}: статус {response.status}")
            return "No description found"
    except Exception as e:
        print(f"Ошибка при получении описания через HTML: {e}")
        return "No description"


async def get_contact_phone_from_html(session, external_id):
    url = f"https://www.bayut.com/property/details-{external_id}.html"
    try:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                html = await response.text()
                soup = BeautifulSoup(html, "html.parser")
                # Проверяем основной селектор
                phone_elem = soup.select_one("span._95c634a6._2454d03d > a > span")
                if phone_elem:
                    return phone_elem.get_text(strip=True)
                # Альтернатива через tel:
                tel_link = soup.find("a", href=lambda x: x and x.startswith("tel:"))
                if tel_link:
                    return tel_link["href"].replace("tel:", "").strip()
                print(f"HTML: Не найден телефон для external_id={external_id}")
                return "No phone found"
            print(
                f"Ошибка загрузки HTML страницы для телефона {external_id}: статус {response.status}"
            )
            return "No phone found"
    except Exception as e:
        print(f"Ошибка получения телефона: {e}")
        return "No phone"


def find_district(district_name):
    if not district_mapping:
        return district_name
    for district, areas in district_mapping.items():
        if district_name in areas:
            return district
    return district_name


def cleanup_old_ids():
    current_time = datetime.now()
    if os.path.exists(CLEANUP_FILE):
        with open(CLEANUP_FILE, "r") as f:
            content = f.read().strip()
            last_cleanup = (
                datetime.fromtimestamp(float(content))
                if content
                else current_time - timedelta(hours=CLEANUP_INTERVAL_HOURS * 2)
            )
        if (current_time - last_cleanup).total_seconds() >= CLEANUP_INTERVAL_HOURS * 3600:
            if os.path.exists(ID_LIST_FILE):
                with open(ID_LIST_FILE, "w") as f:
                    f.write("")
            with open(CLEANUP_FILE, "w") as f:
                f.write(str(current_time.timestamp()))
    else:
        with open(CLEANUP_FILE, "w") as f:
            f.write(str(current_time.timestamp()))


# Чтение списка ID
existing_ids = set()
if os.path.exists(ID_LIST_FILE):
    with open(ID_LIST_FILE, "r") as f:
        existing_ids = set(line.strip() for line in f if line.strip())

# Текущее время
current_time = datetime.now()
start_time = current_time - timedelta(minutes=30)
start_timestamp = int(start_time.timestamp())


async def fetch_hits(session, page):
    data = {
        "requests": [
            {
                "indexName": "bayut-production-ads-en",
                "params": f"hitsPerPage=1000&page={page}&filters=purpose:for-rent&numericFilters=createdAt>{start_timestamp}",
            }
        ]
    }
    async with session.post(
        "https://ll8iz711cs-dsn.algolia.net/1/indexes/*/queries", headers=headers, json=data
    ) as response:
        if response.status == 200:
            return await response.json()
        print(f"Ошибка Algolia API для page={page}: статус {response.status}")
        return {"results": [{"hits": []}]}


async def fetch_detail(session, object_id):
    detail_url = f"{ALGOLIA_BASE_URL}/{object_id}"
    async with session.get(detail_url, headers=headers) as response:
        if response.status == 200:
            return await response.json()
        print(f"Ошибка Algolia API для object_id={object_id}: статус {response.status}")
        return None


async def process_new_ads():
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

            if all_hits:
                new_hits = [hit for hit in all_hits if hit["externalID"] not in existing_ids]
            else:
                new_hits = []

            async with async_session() as db_session:
                async with db_session.begin():
                    for hit in new_hits:
                        external_id = hit["externalID"]
                        object_id = hit.get("objectID")
                        created_at = datetime.fromtimestamp(hit.get("createdAt", 0)).strftime(
                            "%H:%M"
                        )
                        print(
                            f"Обработка: externalID={external_id}, objectID={object_id}, createdAt={created_at}"
                        )
                        if object_id:
                            try:
                                # Проверка на уникальность object_id
                                existing_apartment = await db_session.execute(
                                    select(Apartment).where(Apartment.object_id == object_id)
                                )
                                if existing_apartment.scalars().first():
                                    print(
                                        f"Пропуск: объявление с objectID={object_id} уже существует"
                                    )
                                    continue

                                detail_hit = await fetch_detail(session, object_id)
                                if detail_hit:
                                    owner = await get_contact_phone_from_html(session, external_id)
                                    if owner == "No phone found":
                                        owner = detail_hit.get("phoneNumber", {}).get(
                                            "mobile", "Unknown"
                                        )
                                    name = detail_hit.get("title", "No title")
                                    price = detail_hit.get("price", 0.0)
                                    rooms = str(detail_hit.get("rooms", "Studio"))
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
                                    period = detail_hit.get("rentFrequency", "yearly")
                                    info = await get_info(session, external_id)
                                    if info == "No description found":
                                        keywords = (
                                            ", ".join(detail_hit.get("keywords", [])[:5])
                                            or "Unknown"
                                        )
                                        amenities = (
                                            ", ".join(detail_hit.get("amenities", [])[:3])
                                            or "Unknown"
                                        )
                                        furnishing = detail_hit.get("furnishingStatus", "Unknown")
                                        area = detail_hit.get("area", "Unknown")
                                        baths = detail_hit.get("baths", "Unknown")
                                        info = f"{rooms}-bedroom apartment, {baths} baths, {area} sqm, {furnishing}. Features: {keywords}. Amenities: {amenities}."
                                    print(f"Описание для {external_id}: {info}")
                                    cover_id = detail_hit.get("coverPhoto", {}).get(
                                        "externalID", ""
                                    )
                                    photo_ids = [
                                        str(photo_id) for photo_id in detail_hit.get("photoIDs", [])
                                    ]
                                    if cover_id and str(cover_id) not in photo_ids:
                                        photo_ids.insert(0, str(cover_id))
                                    link = (
                                        f"https://www.bayut.com/property/details-{external_id}.html"
                                    )

                                    apartment_id, matching_clients = await add_apartment(
                                        owner,
                                        name,
                                        price,
                                        rooms,
                                        district,
                                        period,
                                        info,
                                        photo_ids,
                                        object_id,
                                        link,
                                    )
                                    print(
                                        f"Сохранено в БД: ID={apartment_id}, Клиентов: {len(matching_clients)}, Link={link}"
                                    )
                                    stats["successful_adds"] += 1

                                    await send_apartment_notification(apartment_id)
                                else:
                                    print(f"Ошибка API для {external_id}: нет данных")
                            except Exception as e:
                                print(f"Ошибка обработки для {external_id}: {str(e)}")
                            await asyncio.sleep(20)
        finally:
            await session.close()

    if new_hits:
        with open(ID_LIST_FILE, "a") as f:
            for hit in new_hits:
                f.write(f"{hit['externalID']}\n")
        with open(LOG_FILE, "a") as f:
            for hit in new_hits:
                f.write(
                    f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - ID: {hit['externalID']}, Title: {hit['title']}\n"
                )
        print(f"Найдено новых объявлений: {len(new_hits)}")
        for hit in new_hits[:10]:
            print(f"ID: {hit['externalID']}, Title: {hit['title']}, Price: {hit['price']}")
    else:
        print("Нет новых данных.")

    cleanup_old_ids()


if __name__ == "__main__":
    asyncio.run(process_new_ads())
