from telethon import TelegramClient, events
from dotenv import dotenv_values
import cohere
import asyncio
from prompt import prompt_2

env_values = dotenv_values(".env")
api_id = int(env_values.get("C_API_ID"))
api_hash = env_values.get("C_API_HASH")
cohere_api_key = env_values.get("COHERE_API_KEY")

co = cohere.ClientV2(api_key=cohere_api_key)
client = TelegramClient("session_name", api_id, api_hash)

dialogues = {}
allowed_groups = ["Dubai_Chat_2"]


async def generate_response(user_id, user_message):
    """Формирование ответа через Cohere."""
    try:
        if user_id not in dialogues:
            dialogues[user_id] = []

        dialogues[user_id].append({"role": "user", "content": user_message})
        dialogues[user_id] = dialogues[user_id][-20:]  # Ограничение на 20 сообщений

        await asyncio.sleep(1.6)  # Задержка между запросами

        response = co.chat(
            model="command-r7b-12-2024",
            messages=[{"role": "system", "content": prompt_2}] + dialogues[user_id],
            max_tokens=100,
        )

        bot_reply = response.message.content if response.message else ""

        if bot_reply:
            dialogues[user_id].append({"role": "assistant", "content": bot_reply})
            return bot_reply
        else:
            return "999"  # Игнорируем нерелевантные сообщения
    except Exception as e:
        return f"Ошибка: {str(e)}"


@client.on(events.NewMessage)
async def handle_new_message(event):
    chat = await event.get_chat()
    chat_username = chat.username
    if chat_username not in allowed_groups:
        return
    chat_title = chat.title if hasattr(chat, "title") else "ЛС/Неизвестный чат"
    user_message = event.message.message
    sender = await event.get_sender()
    user_id = sender.id

    print(f"[Чат: {chat_title}] {sender.first_name}: {user_message}")

    response = await generate_response(user_id, user_message)
    if response == "999":  # Игнорируем нерелевантные сообщения
        return

    print(f"Бот отвечает в {chat_title}: {response}")
    await event.reply(response)
    await asyncio.sleep(5)  # Задержка перед следующим сообщением


async def main():
    await client.start()
    print("Бот запущен!")
    await client.run_until_disconnected()


with client:
    client.loop.run_until_complete(main())
