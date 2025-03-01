from telethon import TelegramClient, events
import cohere
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
        # Добавляем сообщение пользователя в историю
        if user_id not in dialogues:
            dialogues[user_id] = []

        dialogues[user_id].append({"role": "user", "content": user_message})

        # Ограничиваем историю 20 последними сообщениями (чтобы не перегружать API)
        dialogues[user_id] = dialogues[user_id][-20:]

        # Запрос к Cohere с историей
        response = co.chat(
            model="command-r7b-12-2024",
            messages=dialogues[user_id],  # Передаем всю историю
            max_tokens=200,  # Даем больше места для ответа
        )

        print("Полный ответ Cohere:", response)  # 👀 Выводим ответ API

        # Извлекаем текст
        if response.message and response.message.content:
            bot_reply = response.message.content[0].text.strip()
            # Добавляем ответ бота в историю
            dialogues[user_id].append({"role": "assistant", "content": bot_reply})

            return bot_reply
        else:
            return "Ошибка: API не вернул текст."
    except Exception as e:
        return f"Ошибка при обработке ответа: {str(e)}"


@client.on(events.NewMessage(incoming=True))
async def handle_new_message(event):
    user_message = event.message.message
    sender = await event.get_sender()
    user_id = sender.id  # Получаем ID отправителя

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
