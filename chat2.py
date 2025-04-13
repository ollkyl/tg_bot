import asyncio
from telethon import TelegramClient, events
from dotenv import dotenv_values
import cohere
from prompt import prompt_2

# Загружаем переменные окружения
env_values = dotenv_values(".env")
api_id = int(env_values.get("C_API_ID"))
api_hash = env_values.get("C_API_HASH")
cohere_api_key = env_values.get("COHERE_API_KEY")

# Инициализируем клиента Cohere и Telethon
co = cohere.ClientV2(api_key=cohere_api_key)
client = TelegramClient("session_name", api_id, api_hash)

allowed_groups = [
    "1848872259",
    "1579548825",
    "1509632160",
    "1522020564",
]


async def generate_response(user_message):
    """Формирование кода-ответа через Cohere без сохранения истории."""
    try:
        await asyncio.sleep(1.6)  # Задержка между запросами

        response = co.chat(
            model="command-r7b-12-2024",
            messages=[
                {"role": "system", "content": prompt_2},
                {"role": "user", "content": user_message},
            ],
            max_tokens=50,
        )

        bot_reply = (
            response.message.content[0].text.strip()
            if response.message and response.message.content
            else "999"
        )
        print(f"BOT REPLY: {bot_reply}")
        return bot_reply
    except Exception as e:
        return f"Ошибка: {str(e)}"


@client.on(events.NewMessage)
async def handle_new_message(event):
    chat = await event.get_chat()
    if str(chat.id) not in allowed_groups:
        return

    user_message = event.message.message
    sender = await event.get_sender()

    print(
        f"[Чат: {chat.title if hasattr(chat, 'title') else 'ЛС'}] {sender.first_name}: {user_message}"
    )

    response_code = await generate_response(user_message)

    if response_code == "999":
        print("Сообщение нерелевантное, игнорируем.")
        return
    elif response_code == "AD":
        advertisement_text = (
            "Попробуйте FindApartmentsBot.  подбирает варианты под нужные параметры."
        )
        print(f"✅✅✅Бот отвечает: {advertisement_text}")
        await event.reply(advertisement_text)
    else:
        print(f"Получен неизвестный код: {response_code}")

    await asyncio.sleep(5)


async def main():
    await client.start()
    print("Бот запущен!")
    await client.run_until_disconnected()


with client:
    client.loop.run_until_complete(main())
