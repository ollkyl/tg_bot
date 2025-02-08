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
    "dubaichat_rusarenda_dubai_oae",
    "dubai_chat_1",
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
                    # Если сообщение содержит медиа (не важно одно или альбом)
                    if msg.media:
                        individual_messages.append(msg)  # Это медиа-сообщение
                    else:
                        individual_messages.append(
                            msg
                        )  # Это текстовое сообщение без медиа

            # Пересылаем альбомы
            for album in albums.values():
                await forward_album(client, channels_with_photos, album)

            # Пересылаем обычные сообщения
            for msg in individual_messages:
                if msg.media:  # Если медиа, то пересылаем как в channels_with_photos
                    await forward_to_channels(client, channels_with_photos, msg)
                else:  # Если это текстовое сообщение, то в channels_without_photos
                    await forward_to_channels(client, channels_without_photos, msg)

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
            print(f"✅ Альбом переслан в {channel}")
        except ChatWriteForbiddenError:
            print(f"❌ Нет прав на отправку в {channel}")
        except Exception as e:
            print(f"❌ Ошибка пересылки в {channel}: {e}")


async def forward_to_channels(client, channels, message):
    """Пересылает одиночное сообщение"""
    for channel in channels:
        try:
            await client.forward_messages(channel, message)
            print(f"✅ Сообщение переслано в {channel}")
        except ChatWriteForbiddenError:
            print(f"❌ Нет прав на отправку в {channel}")
        except Exception as e:
            print(f"❌ Ошибка пересылки в {channel}: {e}")


if __name__ == "__main__":
    asyncio.run(send_latest_posts())
