from telethon import TelegramClient
from dotenv import dotenv_values
import asyncio

env_values = dotenv_values(".env")  # Загружаем .env в виде словаря

api_id = int(env_values.get("API_ID"))
api_hash = env_values.get("API_HASH")

# Группа, куда будем пересылать сообщения
channels = ["Zelenogradk", "obshchalka0"]


async def send_latest_posts():
    async with TelegramClient("session_name", api_id, api_hash) as client:
        while True:
            # Получаем последние 5 сообщений из "Saved Messages"
            saved_messages = await client.get_messages("me", limit=5)
            if saved_messages:
                for message in saved_messages:
                    for channel in channels:
                        try:
                            await client.forward_messages(channel, message)
                            print(f"Пост отправлен в {channel}")

                        except Exception as e:
                            print(f"Ошибка отправки в {channel}: {e}")
                    await asyncio.sleep(5)  # Пауза между отправками
            else:
                print("Нет сообщений в сохраненном чате.")

            await asyncio.sleep(2)  # Пауза перед следующим циклом


if __name__ == "__main__":
    asyncio.run(send_latest_posts())
