from telethon import TelegramClient
from dotenv import dotenv_values
import asyncio
from telethon.errors import ChatWriteForbiddenError


env_values = dotenv_values(".env")

api_id = int(env_values.get("C_API_ID"))
api_hash = env_values.get("C_API_HASH")
print(api_id)


channels_banned = [
    "Dubaichatlife",
    "rent_dubai_apt",
    "dubaihome2",
    "dubai_helps",
    "dubaichat_rus",
    "dubai_cha",
    "arenda_dubai_oae",
    "dubai_rentt",
    "myhomeindubai",
    "arenda_dubaii",
    "dubai_appart",
    "poisk_dubai",
    "uae_apartments_rent",
    "depaldo_chat",
    "dubai_baraxolka",
    "dirham_dubai",
    "ryska_Dubai",
    "dubai_ukraine",
    "dubai_chat_russians",
    "kyrgyzy_v_dubaee",
    "sharjashat",
    "dubai_chat_russia",
    "vDubai_rus",
    "dubai_chatt",
    "Emiraty_Dubai",
    "dubairenta",
    "uae_chat_travel",
    "DubaiRentArenda",
    "abu_rent",
    "nedviga_dubai",
    "uae_brokers",
    "dubaysk_arenda",
]

channels_without_links = [
    "my_dubai_chat",
    "oae_realestate_dubai",
    "dubai_chat_rus",
    "rent_dubai1",
    "dubai_rent_uae",
    "oae_realestate_dubai",
    "UAE_DOM/42",
    "UAE_DOM/11",
    "UAE_DOM/49",
    "UAE_DOM/83",
    "UAE_DOM/79",
    "dubaionline247",
    "ours_chat_dubai",
    "ours_main_ads_are_bot",
    "Dubai_Go_Travel",
    "dubai_propertyy",
]

channels_with_links = [
    "sky_property/11",
    "sky_property",
    "dubai_yana_nedvizhimost",
    "uae_talk_Dubai",
    "realstate_in_dubai",
    "hhjij8",
    "DubaiSP4",
    "dubai_chat11",
    "dubai_rr",
    "businessdealuae",
    "vse_svoi_dubai",
    "nedvij_dubai_chat",
    "chat_obmenka",
    "chatdubae",
    "Roomydubai_group",
    "ChatYDubai",
    "dubai_chat_1",
    "DubaiBaraholaka",
    "dubai_uae",
    "dubai_diamond",
    "russians_in_dubaii",
    "ads_dubai",
    "inspacesDubaiRent",
    "rentapartment_dubai_uae",
    "my_dubai_chat",
    "dubai_rent_uae",
    "tutdubai",
    "dubai_dlya_svoih",
    "dubai_chat_biznes",
    "Kazakhstan_dubai_uae",
    "dubaiApartments1",
    "reklamadlyavsehuae",
    "dubaiclubgirls",
    "dubai_uae_oae_russkiye_v_dubae",
    "dubaichatik1",
    "kazakhcommunityuae",
    "uazbekindubai",
    "placeget",
    "Emiraty_Dubai/14573",
    "dubairealtyinvest/1152",
    "dubai_main",
]
# channels_without_links = [
#     "my_dubai_chat",
#     "oae_realestate_dubai",
#     "Dubaichatlife",
#     "uae_chat_travel",
#     "dubai_chat_rus",
#
#     "rent_dubai_apt",
#     "rent_dubai1",
#     "dubaihome2",
#     "dubai_helps",
#     "dubaichat_rus",
#     "dubai_rent_uae",
#     "dubai_cha",
#     "arenda_dubai_oae",
#     "dubai_rentt",
#     "myhomeindubai",
#     "arenda_dubaii",
#     "dubai_appart",
#     "oae_realestate_dubai",
#     "poisk_dubai",
#     "UAE_DOM/42",
#     "UAE_DOM/11",
#     "UAE_DOM/49",
#     "UAE_DOM/83",
#     "UAE_DOM/79",
#     "dubaionline247",
#     "ours_chat_dubai",
#     "ours_main_ads_are_bot",
#     "Dubai_Go_Travel",
#     "dubai_propertyy",
#     "dubai_chat_rus",
# ]

# channels_with_links = [
#     "sky_property/11",
#     "sky_property",
#     "dubai_yana_nedvizhimost",
#     "uae_talk_Dubai",
#     "realstate_in_dubai",
#     "hhjij8",
#     "DubaiSP4",
#     "dubai_chat11",
#     "dubai_rr",
#     "businessdealuae",
#     "vse_svoi_dubai",
#     "nedvij_dubai_chat",
#     "chat_obmenka",
#     "chatdubae",
#     "uae_brokers",
#     "Roomydubai_group",
#     "ChatYDubai",
#     "dubai_chat_1",
#     "DubaiBaraholaka",
#     "dubai_uae",
#     "dubai_diamond",
#     "russians_in_dubaii",
#     "ads_dubai",
#     "inspacesDubaiRent",
#     "rentapartment_dubai_uae",
#     "dubaysk_arenda",
#     "my_dubai_chat",
#     "Dubaichatlife",
#
#     "poisk_dubai",
#     "DubaiRentArenda",
#     "rent_dubai_apt",
#     "rent_dubai1",
#     "dubaihome2",
#     "dubai_cha",
#     "arenda_dubai_oae",
#     "dubai_helps",
#     "dubaichat_rus",
#     "dubai_rentt",
#     "myhomeindubai",
#     "arenda_dubaii",
#     "dubai_appart",
#     "dubai_rent_uae",
#     "uae_apartments_rent",
#     "tutdubai",
#     "depaldo_chat",
#     "dubai_dlya_svoih",
#     "dubai_chat_biznes",
#     "Kazakhstan_dubai_uae",
#     "dirham_dubai",
#     "dubaiApartments1",
#     "ryska_Dubai",
#     "dubai_ukraine",
#     "dubai_chat_russians",
#     "kyrgyzy_v_dubaee",
#     "reklamadlyavsehuae",
#     "dubaiclubgirls",
#     "dubai_uae_oae_russkiye_v_dubae",
#     "dubaichatik1",
#     "kazakhcommunityuae",
#     "uazbekindubai",
#     "sharjashat",
#     "dubai_chat_russia",
#     "placeget",
#     "dubai_chatt",
#     "Emiraty_Dubai/14573",
#     "dubairealtyinvest/1152",
#     "abu_rent",
#     "nedviga_dubai",
#     "dubai_main",
#     "dubairenta",
# ]


sent_messages = set()


async def send_latest_posts():
    async with TelegramClient(
        "session_name", api_id, api_hash, system_version="4.16.30-vxCUSTOM"
    ) as client:
        while True:
            # Пересылаем обычные сообщения
            individual_messages = [
                " 📌 Лайфхак для тех, кто ищет жильё в Дубае! \n Бот @FindApartmentsBot сам подберёт варианты по вашим параметрам и отправит лучшие предложения. Просто попробуйте!\n #Сдам #аренда #квартира #студия #жилье ",
                "Кто ищет квартиру в Дубае, попробуйте @FindApartmentsBot. Я наткнулась на него недавно — он сам подбирает варианты под нужные параметры. Экономит кучу времени!\n #Сдам #аренда #квартира #студия #жилье ",
                "🏡 Хотите быстро найти квартиру в Дубае? \n Попробуйте @FindApartmentsBot — бот сам ищет лучшие варианты и отправляет вам. Удобно, быстро и бесплатно.\n #Сдам #аренда #квартира #студия #жилье ",
                " Ищете квартиру в Дубае? \nЕсть бот, который делает это за вас — @FindApartmentsBot. Проверить легко, просто напишите ему.\n #Сдам #аренда #квартира #студия #жилье ",
                "📌 Лайфхак для тех, кто ищет жильё в Дубае! \n Не тратьте время на бесконечные объявления. Бот @FindApartmentsBot сам подберёт варианты по вашим параметрам и отправит лучшие предложения. Просто попробуйте!\n #Сдам #аренда #квартира #студия #жилье ",
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

            print(f"✅ Сообщение переслано в {channel}")

        except ChatWriteForbiddenError:
            print(f"❌ Нет прав на отправку в {channel}")
        except Exception as e:
            print(f"❌ Ошибка пересылки в {channel}: {e}")

    print(" forward_to_channelstttttttttttttttttt")
    await asyncio.sleep(30)


if __name__ == "__main__":
    asyncio.run(send_latest_posts())
