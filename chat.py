from telethon import TelegramClient, events
import cohere
from dotenv import dotenv_values
import json

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
    [f"🏠 {apt['name']}\n📍 {apt['address']}\n💰 {apt['price']}" for apt in apartments]
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
            model="command-r",
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
            "Ты — риелтор, и к тебе пишет клиент, который увидел твое объявление о квартире. "
            "Общайся дружелюбно, но по делу и на вы.\n\n"
            "📌 Для начала уточни, о какой квартире идет речь, если клиент сразу не указал. "
            f"Вот список доступных квартир: {apartments_str}.\n\n"
            "📌 Если клиент просит подробную информацию по текущей квартире или запрашивает подробную информацию о другой, отвечай в таком формате:\n\n"
            "🏠 *{apartment_name}*\n"
            "📍 *Адрес:* {address}\n"
            "💰 *Цена:* {price}\n"
            "📌 Если клиент просит подробности, но у тебя нет этой информации, не придумывай факты, не пиши сухое 'не знаю', а ответь дружелюбно:\n"
            "👉 'Я уточню у собственника и скоро вам отпишусь!'\n"
            "👉 'Сейчас такой информации нет, но могу узнать. Вам что-то конкретное важно?'\n\n"
            "📌 Отвечай кратко (1-2 предложения), но естественно.\n\n"
            "📌 Если клиент готов к просмотру, предложи договориться о времени:\n"
            "👉 'Отлично! Давайте согласуем удобное время для просмотра. Когда вам удобно?'\n\n"
            "📌 Если клиент пишет что-то странное (например, оскорбления или несвязные вопросы), просто переведи разговор в нужное русло:\n"
            "👉 'Я здесь, чтобы помочь вам с поиском квартиры! Какая информация вам нужна?'\n"
            "👉 'Не совсем понял(а) вас. Вы ищете квартиру?'\n\n"
            "📌 Не используй формальные фразы вроде 'К вашему вниманию', 'Я рад, что вы написали' и т.п. Говори проще и живее.\n\n"
            f"Клиент пишет: {user_message}. Ответь ему."
        )

        response = generate_response(user_id, prompt)

        #     "Ты риелтор. Тебе пишет клиент, который увидел твое объявление о квартире. "
        #     f"Для начала нужно уточнить, о какой квартире идет речь. Вот список доступных квартир: {apartments_str} "
        #     "Больше квартир нет. Если клиент просит подробную информацию по текущей квартире или запрашивает подробную информацию о другой, "
        #     "отвечай в таком формате:\n\n"
        #     "🏠 *{apartment_name}*\n"
        #     "📍 *Адрес:* {address}\n"
        #     "💰 *Цена:* {price}\n"
        #     "🖼️ *Фото:*\n\n"
        #     "Цена не изменна. Ты должен отвечать только на основе реальной информации о квартирах. "
        #     "Если клиент задает вопрос, на который информация не предоставлена, напиши: "
        #     "'К сожалению, не могу точно сказать, отпишусь вам, как уточню у собственника.'\n\n"
        #     "или 'На это у меня, к сожалению, нет ответа' Выбери то что больше подходит по контексту."
        #     "Отвечай на вопросы клиента кратко, в одно или максимум три предложения. "
        #     "Если клиент готов на просмотр квартиры, ответь ему: 'Отлично! Тогда давайте договоримся о просмотре. Когда вам удобно будет?'\n\n"
        #     f"Клиент пишет: {user_message}. Ответь ему."
        # )

    else:
        response = generate_response(user_id, user_message)
        entity = await client.get_entity(user_id)

        if "🏠" in response:
            for apartment in apartments:
                if apartment["name"].lower() in response.lower():
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
