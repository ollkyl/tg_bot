from telethon import TelegramClient, events
import requests
import os
from dotenv import dotenv_values
import json
import time
from fuzzywuzzy import fuzz


env_values = dotenv_values(".env")

api_id = int(env_values.get("API_ID"))
api_hash = env_values.get("API_HASH")
apartments_file = env_values.get("APARTMENTS_FILE", "apartments.json")
url = "https://minitoolai.com/api/chatgpt/"
bearer = env_values.get("BEARER")
headers = {
    "Authorization": bearer,
    "Content-Type": "application/json",
}


def load_prompt(filename="prompt.txt"):
    with open(filename, "r", encoding="utf-8") as f:
        return f.read()


prompt = load_prompt()

try:
    with open(apartments_file, "r", encoding="utf-8") as f:
        apartments = json.load(f)
except Exception as e:
    print(f"Ошибка загрузки файла квартир: {e}")
    apartments = []

apartments_str = "\n".join(
    [
        f" {apt['name']}\n {apt['address']}\n {apt['price']}\n  {apt['info']}\n "
        for apt in apartments
    ]
)


# Создаем клиент Telegram
client = TelegramClient("session_name", api_id, api_hash)

# Хранение диалогов пользователей
dialogues = {}


async def send_apartment_photo(user_id, apartment_id):
    """Отправка фото."""
    for apartment in apartments:
        if apartment["id"] == apartment_id:
            # Отправляем фото и сообщение
            await client.send_file(user_id, apartment["photo"])


def generate_response(user_id, user_message):
    try:
        if user_id not in dialogues:
            dialogues[user_id] = []

        # Добавляем новое сообщение пользователя в историю
        dialogues[user_id].append({"role": "user", "content": user_message})

        data = dialogues[user_id]

        while True:
            response = requests.post(url, headers=headers, json=data, timeout=20)

            if response.status_code != 200:
                print("Ошибка: сервер не ответил корректно.")
            else:
                try:
                    json_str = response.text
                    json_str = json_str.replace("data:", "")
                    json_str = json_str.replace("\n", "")

                    json_str = "[" + json_str.replace("} {", "}, {") + "]"
                    response_data = json.loads(json_str)
                    if all(
                        item.get("content", "").strip() == "" for item in response_data
                    ):
                        print(f"Текст ответа: {response.text}")
                        print("Пустой API")
                    else:
                        bot_reply = ""
                        for item in response_data:
                            bot_reply += item["content"]
                        print(bot_reply)
                        # Добавляем ответ бота в историю
                        dialogues[user_id].append(
                            {"role": "assistant", "content": bot_reply}
                        )
                        return bot_reply
                except json.JSONDecodeError:
                    print(response.text)

    except requests.RequestException as e:
        print(response.text)
        return f"Ошибка запроса к API: {str(e)}"


@client.on(events.NewMessage(incoming=True))
async def handle_new_message(event):
    user_message = event.message.message
    sender = await event.get_sender()
    user_id = sender.id  # Получаем ID отправителя

    if not event.is_private:  # Игнорируем все, кроме личных сообщений
        return

    print(f"Новое сообщение от {sender.username}: {user_message}")

    # Если это первое сообщение в диалоге, даем специальный ответ
    if user_id not in dialogues:
        response = generate_response(user_id, prompt)

    else:
        time.sleep(8)
        response = generate_response(user_id, user_message)
        entity = await client.get_entity(user_id)

        ##TO DO name change to id
        if response.count("🟣") == 1:
            for apartment in apartments:
                response_cleaned = response.lower()
                if fuzz.partial_ratio(apartment["name"].lower(), response_cleaned) > 80:
                    await send_apartment_photo(user_id, apartment["id"])
                    break

        if "уточню у собственника" in response:
            await client.send_message(
                "me",
                f"( клиент @{entity.username} ждет ответ собственника)",
            )
        if "вам удобно будет?" in response or "вам удобно будет?" in response:
            await client.send_message(
                "me", f"( клиент @{entity.username} хочет записаться на просмотр"
            )

    # Отправляем ответ
    await event.reply(response)
    print(f"Ответ отправлен: {response}")


async def main():
    await client.start()
    print("Авторизация прошла успешно!")

    me = await client.get_me()
    print(f"Я вошел как: {me.first_name} ({me.username})")

    await client.run_until_disconnected()


# Запускаем клиент
with client:
    client.loop.run_until_complete(main())
