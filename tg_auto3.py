from telethon import TelegramClient
from dotenv import dotenv_values
import asyncio
from telethon.errors import ChatWriteForbiddenError


env_values = dotenv_values(".env")  # Загружаем .env в виде словаря

api_id = int(env_values.get("API_ID"))
api_hash = env_values.get("API_HASH")

# Группы, куда пересылаем сообщения
channels_with_photos = [
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
    "ffghhhkkmn",
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
    "dubai_chat_russia"
]  # Сюда пересылаем только текстовые сообщения

sent_messages = set()  # Храним ID уже пересланных сообщений


async def send_latest_posts():
    async with TelegramClient(
        "session_name", api_id, api_hash, system_version="4.16.30-vxCUSTOM"
    ) as client:
        while True:
            saved_messages = await client.get_messages(
                "me", limit=20
            )  # Берём 20 последних сообщений

            if not saved_messages:
                print("⚠ Нет новых сообщений в сохраненных.")
                await asyncio.sleep(30)  # Ждём 30 сек перед следующей проверкой
                continue

            albums = {}  # Словарь для группировки сообщений по grouped_id
            individual_messages = []  # Сообщения без группировки

            # Группируем сообщения
            for msg in saved_messages:
                if msg.grouped_id:
                    albums.setdefault(msg.grouped_id, []).append(msg)
                else:
                    individual_messages.append(msg)  # Это текстовое сообщение без медиа

                # Пересылаем альбомы

            async def album_task():
                for album in albums.values():
                    await forward_album(client, channels_with_photos, album)
                    await asyncio.sleep(4400)

                # Пересылаем обычные сообщения

            async def msg_task():
                for msg in individual_messages:
                    await forward_to_channels(client, channels_without_photos, msg)
                    await asyncio.sleep(4400)

            await asyncio.gather(album_task(), msg_task())

            print("⚠ Ожидание 30 секунд перед новой проверкой...")
            await asyncio.sleep(30)  # Ждём перед следующей проверкой


async def forward_album(client, channels, album):
    """Пересылает весь альбом целиком (фото, видео) с текстом"""
    # Находим сообщение с текстом (обычно он в последнем)
    text = next((msg.message for msg in reversed(album) if msg.message), "")

    media_group = [msg for msg in album]  # Все вложения из альбома

    for channel in channels:
        try:
            await client.send_file(
                channel,
                [msg.media for msg in media_group],  # Отправляем весь альбом
                caption=text if text else None,  # Добавляем текст, если он есть
            )
            await asyncio.sleep(3)
            print(f"✅ Альбом переслан в {channel}")
        except ChatWriteForbiddenError:
            print(f"❌ Нет прав на отправку в {channel}")
            await asyncio.sleep(3)
        except Exception as e:
            print(f"❌ Ошибка пересылки в {channel}: {e}")
            await asyncio.sleep(3)
    print(" forward_albumtttttttttttttttttt")
    await asyncio.sleep(30)


async def forward_to_channels(client, channels, message):
    """Пересылает одиночное сообщение"""
    for channel in channels:
        try:
            await client.forward_messages(channel, message)
            await asyncio.sleep(3)
            print(f"✅ Сообщение переслано в {channel}")

        except ChatWriteForbiddenError:
            print(f"❌ Нет прав на отправку в {channel}")
            await asyncio.sleep(3)
        except Exception as e:
            await asyncio.sleep(3)
            print(f"❌ Ошибка пересылки в {channel}: {e}")
            await asyncio.sleep(3)
    print(" forward_to_channelstttttttttttttttttt")
    await asyncio.sleep(30)


if __name__ == "__main__":
    asyncio.run(send_latest_posts())
