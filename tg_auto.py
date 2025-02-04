from telethon import TelegramClient
from dotenv import dotenv_values
import asyncio
from telethon.errors import ChatWriteForbiddenError


env_values = dotenv_values(".env")  # Загружаем .env в виде словаря

api_id = int(env_values.get("API_ID"))
api_hash = env_values.get("API_HASH")

# Группы, куда пересылаем сообщения
channels_with_photos = [
    "sky_property",
    "dubai_yana_nedvizhimost",
    "my_dubai_chat",
    "uae_talk_Dubai",
    "realstate_in_dubai",
    "hhjij8",
    "Dubaichatlife",
    "DubaiSP4",
    "dubai_chat11",
    "dubai_rr",
    "uae_chat_travel",
    "poisk_dubai",
    "dubai_rus_chat",
    "businessdealuae",
    "vse_svoi_dubai",
    "dubai_chat_rus",
    "DubaiRentArenda",
    "nedvij_dubai_chat",
    "dubai_chat_ads",
    "oae_realestate_dubai",
    "chat_obmenka",
    "DubaiCIAN",
    "chatdubae",
    "rent_dubai_apt",
    "rent_dubai1",
    "uae_brokers",
    "dubaihome2",
    "RealtyDubay",
    "realestate_dxb_uae",
    "dubaiapartments2022",
    "Roomydubai_group",
    "dubai_nadvizh",
    "ChatYDubai",
    "UAEDubai_Realty",
    "dubai_cha",
    "arenda_dubai_oae",
    "dubai_chat_1",
    "arenda_dubaysk",
    "DubaiBaraholaka",
    "dubai_uae",
    "dubai_diamond",
    "dubai_helps",
    "dubaichat_rus",
    "russians_in_dubaii",
    "ads_dubai",
    "inspacesDubaiRent",
    "dubai_rentt",
    "myhomeindubai",
    "arenda_dubaii",
    "dubai_appart",
    "rentapartment_dubai_uae",
    "homes_dubai",
    "dubaysk_arenda",
    "dubai_rent_uae",
    "dubai_propertyy",
    "uae_apartments_rent",
]  # Сюда пересылаем только сообщения с фото

channels_without_photos = [
    "perviv_dubae",
    "tutdubai",
    "chatoae",
    "realestate_dubai_rus",
    "Dubai_Go_Travel",
    "dubai1top",
    "depaldo_chat",
    "dubai_dlya_svoih",
    "dubai_chat_biznes",
    "Kazakhstan_dubai_uae",
    "Dubaydagi_Uzbeklarr",
    "dubai_baraxolka",
    "dirham_dubai",
    "dubaiApartments1",
    "ryska_Dubai",
    "dubai_barakholka",
    "dubai_ukraine",
    "dubai_chat_russians",
    "kyrgyzy_v_dubaee",
    "reklamadlyavsehuae",
    "dubaiclubgirls",
    "dubai_uae_oae_russkiye_v_dubae",
    "dubaichatik1",
    "kazakhcommunityuae",
    "kyrgysz_in_dubai",
    "uazbekindubai",
    "dubaionline247",
    "sharjashat",
    "design467",
    "dubai_chat_russia",
]  # Сюда пересылаем только текстовые сообщения


async def send_latest_posts():
    async with TelegramClient("session_name", api_id, api_hash) as client:
        while True:
            saved_messages = await client.get_messages(
                "me", limit=20
            )  # Берем последние 20 сообщений

            if not saved_messages:
                print("⚠ Нет новых сообщений в сохраненных.")
                await asyncio.sleep(
                    30
                )  # Если сообщений нет, ждем 30 сек и пробуем снова
                continue

            messages_with_photos = [msg for msg in saved_messages if msg.media]
            messages_without_photos = [msg for msg in saved_messages if not msg.media]

            while messages_with_photos and messages_without_photos:
                photo_msg = messages_with_photos.pop(0)  # Берем одно сообщение с фото
                text_msg = messages_without_photos.pop(
                    0
                )  # Берем одно текстовое сообщение

                await asyncio.gather(
                    send_to_channels(client, channels_with_photos, photo_msg),
                    send_to_channels(client, channels_without_photos, text_msg),
                )

                print("⏳ Пауза 30 секунд перед следующей парой сообщений...")
                await asyncio.sleep(30)  # Пауза после отправки пары сообщений

            print("⚠ Сообщения закончились. Ждем 30 секунд перед новой проверкой.")
            await asyncio.sleep(
                30
            )  # Если сообщений не осталось, ждем перед новой проверкой


async def send_to_channels(client, channels, message):
    """Отправляет сообщение во все указанные каналы"""
    for channel in channels:
        try:
            await client.forward_messages(channel, message)
            print(f"✅ Сообщение отправлено в {channel}")
        except ChatWriteForbiddenError:
            print(f"❌ Нет прав на отправку в {channel}")
        except Exception as e:
            print(f"❌ Ошибка отправки в {channel}: {e}")


if __name__ == "__main__":
    asyncio.run(send_latest_posts())
