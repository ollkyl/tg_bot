from telethon import TelegramClient
from telethon import events
import os
import asyncio
import openai
from dotenv import load_dotenv

load_dotenv()

api_id = os.getenv("API_ID")
api_hash = os.getenv("API_HASH")
phone = os.getenv("PHONE_NUMBER")
openai.api_key = os.getenv("OPENAI_API_KEY")

# Создаем клиент
client = TelegramClient("session_name", api_id, api_hash)


async def main():
    # Авторизация (если сессия уже существует, повторная авторизация не потребуется)
    await client.start()
    print("Авторизация прошла успешно!")

    # Получаем информацию о себе
    me = await client.get_me()
    print(f"Я вошел как: {me.first_name} ({me.username})")


# Запускаем клиент
with client:
    client.loop.run_until_complete(main())


def generate_response(prompt):
    response = openai.Completion.create(
        engine="text-davinci-003",  # или "gpt-4", если у вас доступ
        prompt=prompt,
        max_tokens=150,
        temperature=0.7,
    )
    return response.choices[0].text.strip()


@client.on(events.NewMessage(incoming=True))
async def handle_new_message(event):
    # Получаем текст сообщения
    user_message = event.message.message
    sender = await event.get_sender()
    print(f"Новое сообщение от {sender.username}: {user_message}")

    # Генерируем ответ с помощью нейросети
    prompt = f"Ты риелтор. Клиент пишет: {user_message}. Ответь ему."
    response = generate_response(prompt)

    # Отправляем ответ
    await event.reply(response)
    print(f"Ответ отправлен: {response}")


# Запускаем клиент
with client:
    client.loop.run_until_complete(main())
    client.run_until_disconnected()


@client.on(events.NewMessage(incoming=True))
async def handle_meet_message(event):
    user_message = event.message.message
    sender = await event.get_sender()

    if "записаться на просмотр" in user_message.lower():
        await event.reply("Пожалуйста, укажите удобную дату и время для просмотра.")
    elif "дата" in user_message.lower() and "время" in user_message.lower():
        await event.reply("Вы успешно записаны на просмотр!")
    else:
        prompt = f"Ты риелтор. Клиент пишет: {user_message}. Ответь ему."
        response = generate_response(prompt)
        await event.reply(response)
