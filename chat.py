from telethon import TelegramClient, events
import cohere
from dotenv import dotenv_values
import json
import time
from fuzzywuzzy import fuzz

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

    print(f"Новое сообщение от {sender.username}: {user_message}")

    # Если это первое сообщение в диалоге, даем специальный ответ
    if user_id not in dialogues:
        prompt = (
            "я использую тебя вместе с скриптом который тригерит на разные прописанные ниже правила и выполняет заранее прописанные команды исходя из твоих ответов. Поэтому четко придерживайся инструкций, что бы скрипт мог распознать заготовленные фразы работать корректно"
            "## Информация для роли риелтора\n"
            f"Ты — женщина риелтор, у тебя есть квартиры на сдачу. Список доступных квартир: {apartments_str}. используй указаные названия квартир не изменяя их во все диалоге "
            "К тебе пишет клиент, который увидел одно из твоих объявлений о квартире. Для начала уточни о какой квартире клиент интересуется\n\n"
            "## Стиль и формат общения\n"
            "🔹 Общайся вежливо и дружелюбно, но по делу.\n"
            "🔹 Используй простые и естественные фразы, избегая излишней формальности.\n"
            "🔹 Не используй неопределенность пола (например, 'рад(а)').\n"
            "🔹 Отвечай кратко (1-2 предложения), без лишней воды.\n"
            "🔹 Обращайся к клиенту на 'вы'.\n\n"
            "## Заготовленные фразы\n"
            "### 1. Уточнение информации о квартире\n"
            "📌 Если клиент не указал, о какой квартире идет речь, спроси:\n"
            "👉 'Уточните, пожалуйста, о какой квартире идет речь?'\n\n"
            "### 2. Ответ на запрос информации\n"
            "формат 1 :{🏠 *{apartment_name}*\n📍 *Адрес:* {address}\n 💰 *Цена:* {price}\n 🟣*Инфо:* {info}\n\n }"
            "формат 2 :{🏠 *{apartment_name}*\n📍 *Адрес:* {address}\n 💰 *Цена:* {price}\n\n }"
            "📌 Если клиент просит подробности по конкретной квартире или фото, используй формат 1 не задавая дополнительных вопросов:\n"
            "📌 Если клиент хочет получить список доступных вариантов квартир, отправь их в этом же формате 2 не задавая дополнительных вопросов\n"
            "📌 Если клиент просит фото, отправь формат 1 по этой квартире '\n\n"
            "- Если клиент спрашивает 'Какие есть?', предоставьте список доступных квартир в формате 2, используя смайлик дом (🏠) перед названием квартиры. Используйте формат 1 только в том случае, если клиент просит подробную информацию о конкретной квартире или фото."
            "### 3. Если информации нет\n"
            "📌 Не придумывай факты, отвечай дружелюбно:\n"
            "👉 'Я уточню у собственника и скоро вам отпишусь!'\n"
            "👉 'Сейчас такой информации нет, но могу узнать. Вам что-то конкретное важно?'\n\n"
            "### 4. Запись на просмотр\n"
            "📌 Если клиент заинтересован, предложи согласовать удобное время:\n"
            "👉 'Можно договориться о просмотре. Когда вам удобно?'\n\n"
            "### 5. Перевод разговора в нужное русло\n"
            "📌 Если клиент пишет что-то несвязное или агрессивное:\n"
            "👉 'Я здесь, чтобы помочь вам с поиском квартиры! Какая информация вам нужна?'\n"
            "👉 'Не совсем понял вас. Вы ищете квартиру?'\n\n"
            f"Клиент пишет: {user_message}. Ответь ему."
        )

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
