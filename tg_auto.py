from telethon import TelegramClient
from dotenv import load_dotenv, dotenv_values

import os
import asyncio

env_values = dotenv_values(".env")  # Загружаем .env в виде словаря
print(f"API_ID из dotenv_values: {env_values.get('API_ID')}")

api_id = os.getenv("API_ID")
api_hash = os.getenv("API_HASH")
print(f"API_ID из .env: {api_id}")

# Группа, куда будем пересылать сообщение
channels = ["Zelenogradk"]


async def send_latest_post():
    async with TelegramClient("session_name", api_id, api_hash) as client:
        # Получаем последнее сообщение из "Saved Messages"
        saved_messages = await client.get_messages("me", limit=1)

        if saved_messages:
            message = saved_messages[0]  # Берем последнее сообщение

            for channel in channels:
                try:
                    await client.forward_messages(channel, message)
                    print(f"✅ Пост отправлен в {channel}")
                    await asyncio.sleep(3670)  # Пауза между отправками
                except Exception as e:
                    print(f"❌ Ошибка отправки в {channel}: {e}")
        else:
            print("❌ Нет сообщений в сохраненном чате.")


if __name__ == "__main__":
    asyncio.run(send_latest_post())
