from telethon import TelegramClient, events
import requests

from dotenv import dotenv_values
import json
from prompt import prompt_1

env_values = dotenv_values(".env")

api_id = int(env_values.get("API_ID"))
api_hash = env_values.get("API_HASH")
cohere_api_key = env_values.get("COHERE_API_KEY")
apartments_file = env_values.get("APARTMENTS_FILE", "apartments.json")

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


# Создаем клиент Cohere
co = cohere.ClientV2(api_key=cohere_api_key)

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
        dialogues[user_id].append({"role": "user", "content": user_message})
        print("DEBUG:", dialogues[user_id])
        print("DEBUG END")
        while True:
            response = requests.post(
                url, headers=headers, json=dialogues[user_id], timeout=20
            )
            if response.status_code != 200:
                print("Ошибка: сервер не ответил корректно.")
            else:
                try:
                    json_str = response.text
                    json_str = json_str.replace("data:", "")
                    json_str = json_str.replace("\n", "")

                    json_str = "[" + json_str.replace("} {", "}, {") + "]"
                    print("Сырой ответ от API:", response.text)

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
                        print(f"бот сгенерил : {bot_reply}")
                        # Добавляем ответ бота в историю
                        dialogues[user_id].append(
                            {"role": "assistant", "content": bot_reply}
                        )
                        return bot_reply
                except json.JSONDecodeError:
                    print("Ошибка декодирования json")

    except requests.RequestException as e:
        return f"Ошибка запроса к API: {str(e)}"


@client.on(events.NewMessage(incoming=True))
async def handle_new_message(event):
    user_message = event.message.message
    sender = await event.get_sender()
    user_id = sender.id  # Получаем ID отправителя
    print(f"Новое сообщение от {sender.username}: {user_message}")
    apartments_str = format_apartments(apartments)
    prompt = load_prompt()
    prompt += "Полный список квартир:\n" + apartments_str

    if not event.is_private:  # Игнорируем все, кроме личных сообщений
        return
    global prompt_1
    print(f"Новое сообщение от {sender.username}: {user_message}")
    prompt_1 = (
        prompt_1
        + f"Список доступных квартир:{apartments_str}"
        + f" клиент пишет :{user_message}"
    )

    # Если это первое сообщение в диалоге, даем специальный ответ
    if user_id not in dialogues:
        response = generate_response(user_id, prompt_1)
        entity = await client.get_entity(user_id)
        await client.send_message(entity, "Добрый день, какая квартира вас интересует?")
    else:
        response = generate_response(user_id, user_message)
        entity = await client.get_entity(user_id)

        # if "11" in response:  #
        #     await client.send_message(entity, "какая квартира вас интересует?")

        if "33" in response:  # apartmrnts
            for ap in apartments:
                formatted_text = (
                    f"⭐️ Сдается {ap['name']}!\n\n"
                    f"📍 {ap['address']}\n"
                    f"💵 Цена: {ap['price']}\n"
                    f"ℹ️ {ap['info']}\n"
                )
                await client.send_message(entity, formatted_text)

        if "34" in response:  # apartmrnts
            response = response[2:]  # убрать 2 первых символа
            id = int(response.strip())
            for ap in apartments:
                if ap["id"] == id:
                    formatted_text = (
                        f"⭐️ Сдается {ap['name']}!\n\n"
                        f"📍 {ap['address']}\n"
                        f"💵 Цена: {ap['price']}\n"
                        f"ℹ️ {ap['info']}\n"
                    )
            await send_apartment_photo(user_id, id)
            await client.send_message(entity, f"{formatted_text}")

        if "36" in response:
            await client.send_message(
                entity, "Мне нужно уточнить этот момент, скоро вернусь к вам с ответом)"
            )
            await client.send_message(
                "me",
                f"( клиент @{entity.username} ждет ответ собственника)",
            )
        if "35" in response:
            await client.send_message(entity, "Отлично, когда вам удобно?")
            await client.send_message(
                "me", f"( клиент @{entity.username} хочет записаться на просмотр"
            )

    print(f"код получен: {response}")


async def main():
    await client.start()
    print("Авторизация прошла успешно!")

    me = await client.get_me()
    print(f"Я вошел как: {me.first_name} ({me.username})")

    await client.run_until_disconnected()


# Запускаем клиент
with client:
    client.loop.run_until_complete(main())
