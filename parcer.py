# parser.py
import asyncio
import aiohttp
import os
import time
from datetime import datetime, timedelta
from db import add_apartment, async_session, Apartment
from sending_messages import send_apartment_notification
from dotenv import dotenv_values
from sqlalchemy.sql import select

# Загрузка переменных окружения
env_values = dotenv_values(".env")
ALGOLIA_BASE_URL = env_values.get("ALGOLIA_BASE_URL")
ALGOLIA_API_KEY = env_values.get("ALGOLIA_API_KEY")
ALGOLIA_APP_ID = env_values.get("ALGOLIA_APP_ID")

# Файлы для хранения
ID_LIST_FILE = "id_list.txt"
CLEANUP_FILE = "cleanup_time.txt"
LOG_FILE = "new_ads.log"
CLEANUP_INTERVAL_HOURS = 12  # Интервал очистки в часах

# Заголовки для запросов
headers = {
    "X-Algolia-API-Key": ALGOLIA_API_KEY,
    "X-Algolia-Application-Id": ALGOLIA_APP_ID,
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/138.0.0.0 Safari/537.36",
}

district_mapping = {
    "Citywalk": [
        "Al Wasl",
        "Al Satwa",
        "Al Jaddaf",
        "Za'abeel",
        "Al Karama",
        "Al Badaa",
        "Al Manara",
        "Al Hudaiba",
    ],
    "Bluewaters": ["Bluewaters Island", "Jumeirah Beach Residence (JBR)"],
    "The Palm Jumeirah": [
        "Palm Jumeirah",
        "Jumeirah",
        "Umm Suqeim",
        "Jumeirah Islands",
        "Emirates Hills",
        "Me'aisem 1",
        "Umm Al Sheif",
        "Pearl Jumeirah",
    ],
    "Dubai Marina": [
        "Dubai Marina",
        "Jumeirah Lake Towers (JLT)",
        "Jumeirah Heights",
        "The Springs",
        "The Meadows",
        "The Lakes",
    ],
    "Business Bay": ["Business Bay", "Sheikh Zayed Road", "World Trade Centre", "Al Safa"],
    "Downtown": ["Downtown Dubai", "DIFC", "Za'abeel", "Bur Dubai", "Al Mina"],
    "DIFC": ["DIFC", "Sheikh Zayed Road", "World Trade Centre"],
    "ZAABEL + DHCC": [
        "Za'abeel",
        "Al Jaddaf",
        "Al Rashidiya",
        "Muhaisnah",
        "Al Twar",
        "Nad Al Hamar",
        "Al Warqaa",
        "Academic City",
    ],
    "Dubai Media City + Dubai Internet City": [
        "Dubai Media City",
        "Dubai Internet City",
        "Barsha Heights (Tecom)",
        "Al Sufouh",
    ],
    "JLT": ["Jumeirah Lake Towers (JLT)", "Jumeirah Heights"],
    "JVC": [
        "Jumeirah Village Circle (JVC)",
        "Arjan",
        "Tilal Al Ghaf",
        "Majan",
        "Serena",
        "City of Arabia",
        "Dubailand",
        "Reem",
        "The Villa",
    ],
    "Meydan: Sobha + Azizi Riviera": [
        "Meydan City",
        "Sobha Hartland",
        "Mohammed Bin Rashid City",
        "Remraam",
        "DAMAC Hills",
        "DAMAC Hills 2 (Akoya by DAMAC)",
        "Al Barari",
        "Falcon City of Wonders",
        "Hadaeq Sheikh Mohammed Bin Rashid",
    ],
    "Dubai Design District + Al Jaddaf": [
        "Al Jaddaf",
        "Dubai Design District",
        "Ras Al Khor",
        "Al Warsan",
        "Dubai Festival City",
    ],
    "JVT": [
        "Jumeirah Village Triangle (JVT)",
        "Jumeirah Park",
        "The Springs",
        "The Meadows",
        "The Greens",
        "The Views",
    ],
    "Creek Harbour": [
        "Dubai Creek Harbour",
        "Nad Al Sheba",
        "Culture Village (Jaddaf Waterfront)",
        "Wadi Al Shabak",
        "Wadi Al Amardi",
    ],
    "Dubai Production City + Sport City + Motor City": [
        "Dubai Production City (IMPZ)",
        "Dubai Sports City",
        "Motor City",
        "Jumeirah Golf Estates",
        "Dubai Science Park",
        "Living Legends",
        "Dubai Studio City",
    ],
    "Al Furjan + Discovery Garden": [
        "Al Furjan",
        "Discovery Gardens",
        "The Gardens",
        "Jebel Ali",
        "Dubai South",
        "Dubai Industrial City",
        "Expo City",
    ],
    "Al Quoz": ["Al Quoz", "Al Khawaneej", "Al Awir", "Al Mizhar", "Mushraif", "Bukadra"],
    "Al Barsha + Arjan": [
        "Al Barsha",
        "Arjan",
        "Barsha Heights (Tecom)",
        "Al Sufouh",
        "Mirdif",
        "Dubai Land Residence Complex",
        "Green Community",
    ],
}


def find_district(district_name):
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
        return {"results": [{"hits": []}]}


async def fetch_detail(session, object_id):
    detail_url = f"{ALGOLIA_BASE_URL}/{object_id}"
    async with session.get(detail_url, headers=headers) as response:
        if response.status == 200:
            return await response.json()
        return None


async def process_new_ads():
    stats = {"successful_adds": 0}
    async with aiohttp.ClientSession() as session:
        try:
            # Запрос к Algolia
            all_hits = []
            page = 0
            while True:
                result = await fetch_hits(session, page)
                hits = result["results"][0]["hits"]
                if not hits:
                    break
                all_hits.extend(hits)
                page += 1
                await asyncio.sleep(1)  # Задержка для API Algolia

            # Обработка
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
                                    owner = detail_hit.get("ownerAgent", {}).get("name", "Unknown")
                                    name = detail_hit.get("title", "No title")
                                    price = detail_hit.get("price", 0.0)
                                    rooms = str(detail_hit.get("rooms", 0))
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
                                    info = detail_hit.get("description", "No description")
                                    cover_id = detail_hit.get("coverPhoto", {}).get("externalID")
                                    photo_ids = [
                                        str(photo_id) for photo_id in detail_hit.get("photoIDs", [])
                                    ]
                                    # Добавляем обложку в начало, если её нет в списке
                                    if cover_id and str(cover_id) not in photo_ids:
                                        photo_ids.insert(0, str(cover_id))
                                    # Формируем ссылку
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
                                    print(f"Ошибка API для {external_id}: статус ")
                            except Exception as e:
                                print(f"Ошибка обработки для {external_id}: {str(e)}")
                            await asyncio.sleep(20)
        finally:
            await session.close()  # Гарантируем закрытие сессии

    # Сохранение новых ID
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


# Запуск асинхронной функции
if __name__ == "__main__":
    asyncio.run(process_new_ads())
