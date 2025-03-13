from telethon import TelegramClient
from dotenv import dotenv_values
import asyncio
from telethon.errors import ChatWriteForbiddenError


env_values = dotenv_values(".env")

api_id = int(env_values.get("C_API_ID"))
api_hash = env_values.get("C_API_HASH")
print(api_id)

# Группы, куда пересылаем сообщения
channels_with_photos = [
    "sky_property",
    "dubai_yana_nedvizhimost",
    "my_dubai_chat",
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
    "krasnodar_chati",
    "realestate_dubai_rus",
    "Dubai_Go_Travel",
    "dubai1top",
    "depaldo_chat",
    "dubai_dlya_svoih",
    "uazbekindubai",
    "dubaionline247",
    "sharjashat",
    "design467",
]  # Сюда пересылаем только текстовые сообщения
channels_without_links = [
    "my_dubai_chat",
    "Dubaichatlife",
    "uae_chat_travel",
    "dubai_chat_rus",
    "DubaiRentArenda",
    "dubai_chat_ads",
    "rent_dubai_apt",
    "rent_dubai1",
    "dubaihome2",
    "RealtyDubay",
    "UAEDubai_Realty",
    "dubai_helps",
    "dubaichat_rus",
    "dubai_rent_uae",
    "dubai_cha",
    "arenda_dubaysk",
    "arenda_dubai_oae",
    "realestate_dxb_uae",
    "dubai_rentt",
    "myhomeindubai",
    "homes_dubai",
    "arenda_dubaii",
    "dubai_appart",
    "dubaiapartments2022",
    "oae_realestate_dubai",
    "poisk_dubai",
]
channels_with_links = [
    "sky_property",
    "dubai_yana_nedvizhimost",
    "uae_talk_Dubai",
    "realstate_in_dubai",
    "hhjij8",
    "DubaiSP4",
    "dubai_chat11",
    "dubai_rr",
    "dubai_rus_chat",
    "businessdealuae",
    "vse_svoi_dubai",
    "nedvij_dubai_chat",
    "chat_obmenka",
    "DubaiCIAN",
    "chatdubae",
    "uae_brokers",
    "Roomydubai_group",
    "dubai_nadvizh",
    "ChatYDubai",
    "dubai_chat_1",
    "DubaiBaraholaka",
    "dubai_uae",
    "dubai_diamond",
    "russians_in_dubaii",
    "ads_dubai",
    "inspacesDubaiRent",
    "rentapartment_dubai_uae",
    "dubaysk_arenda",
    "my_dubai_chat",
    "Dubaichatlife",
    "uae_chat_travel",
    "poisk_dubai",
    "dubai_chat_rus",
    "DubaiRentArenda",
    "dubai_chat_ads",
    "oae_realestate_dubai",
    "rent_dubai_apt",
    "rent_dubai1",
    "dubaihome2",
    "RealtyDubay",
    "realestate_dxb_uae",
    "dubaiapartments2022",
    "UAEDubai_Realty",
    "dubai_cha",
    "arenda_dubai_oae",
    "arenda_dubaysk",
    "dubai_helps",
    "dubaichat_rus",
    "dubai_rentt",
    "myhomeindubai",
    "arenda_dubaii",
    "dubai_appart",
    "homes_dubai",
    "dubai_rent_uae",
    "dubai_propertyy",
    "uae_apartments_rent",
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
    "placeget",
    "vDubai_rus",
    "dubai_chatt",
    "Emiraty_Dubai",
    "dubairealtyinvest",
    "UAE_DOM",
    "abu_rent",
    "ours_chat_dubai",
    "ours_main_ads_are_bot",
    "nedviga_dubai",
    "dubai_main",
    "dubairenta",
]

sent_messages = set()


async def send_latest_posts():
    async with TelegramClient(
        "session_name", api_id, api_hash, system_version="4.16.30-vxCUSTOM"
    ) as client:
        while True:
            # Пересылаем обычные сообщения
            individual_messages = [
                " 📌 Лайфхак для тех, кто ищет жильё в Дубае! \n Бот @FindApartmentsBot сам подберёт варианты по вашим параметрам и отправит лучшие предложения. Просто попробуйте!\n сдается аренда квартира студия жилье ",
                "Кто ищет квартиру в Дубае, попробуйте @FindApartmentsBot. Я наткнулась на него недавно — он сам подбирает варианты под нужные параметры. Экономит кучу времени!",
                "🏡 Хотите быстро найти квартиру в Дубае? \n Попробуйте @FindApartmentsBot — бот сам ищет лучшие варианты и отправляет вам. Удобно, быстро и бесплатно.",
                " Ищете квартиру в Дубае? \nЕсть бот, который делает это за вас — @FindApartmentsBot. Проверить легко, просто напишите ему.",
                "📌 Лайфхак для тех, кто ищет жильё в Дубае! \n Не тратьте время на бесконечные объявления. Бот @FindApartmentsBot сам подберёт варианты по вашим параметрам и отправит лучшие предложения. Просто попробуйте!",
            ]

            async def msg_task():
                for msg in individual_messages:
                    await forward_to_channels(client, channels_with_links, msg)
                    await asyncio.sleep(3650)

            async def msg2_task():
                for msg in individual_messages:
                    msg = msg.replace("@", "")
                    await forward_to_channels(client, channels_without_links, msg)
                    await asyncio.sleep(3650)

            await asyncio.gather(msg_task(), msg2_task())

            print("⚠ Ожидание 30 секунд перед новой проверкой...")
            await asyncio.sleep(30)


async def forward_to_channels(client, channels, message):
    """Пересылает одиночное сообщение"""
    for channel in channels:
        try:
            await client.send_message(channel, message)
            # await client.forward_messages(channel, message)
            await asyncio.sleep(2)
            print(f"✅ Сообщение переслано в {channel}")

        except ChatWriteForbiddenError:
            print(f"❌ Нет прав на отправку в {channel}")
        except Exception as e:
            print(f"❌ Ошибка пересылки в {channel}: {e}")
        await asyncio.sleep(2)
    print(" forward_to_channelstttttttttttttttttt")
    await asyncio.sleep(30)


if __name__ == "__main__":
    asyncio.run(send_latest_posts())
