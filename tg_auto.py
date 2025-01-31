from telethon import TelegramClient
from dotenv import load_dotenv
import os
import asyncio

load_dotenv()

api_id = os.getenv("API_ID")
api_hash = os.getenv("API_HASH")
phone = os.getenv("PHONE_NUMBER")


# Список ID каналов и групп
channels = [
    "Zelenogradk",  # Группа по username
]

# ID сообщения, которое нужно переслать
message_id = 123456  #  ID сообщения, которое нужно переслать
personal_chat = "me"  # Личный чат, из которого будем пересылать сообщение


async def send_posts():
    async with TelegramClient("session_name", api_id, api_hash) as client:
        # 1. Пересылаем сообщение из личного чата в группы
        for channel in channels:
            try:
                # Пересылаем сообщение с указанным ID
                await client.forward_messages(
                    channel, message_id, from_peer=personal_chat
                )

                print(f"✅ Пост отправлен в {channel}")
                await asyncio.sleep(3670)  # Пауза между отправками
            except Exception as e:
                print(f"❌ Ошибка отправки в {channel}: {e}")


if __name__ == "__main__":
    asyncio.run(send_posts())
