from telethon import TelegramClient
from telethon import events
import cohere
from dotenv import dotenv_values

env_values = dotenv_values(".env")

api_id = int(env_values.get("API_ID"))
api_hash = env_values.get("API_HASH")
phone = env_values.get("PHONE")
cohere_api_key = env_values.get("COHERE_API_KEY")

# Создаем клиент Cohere
co = cohere.ClientV2(api_key=cohere_api_key)

# Создаем клиент Telegram
client = TelegramClient("session_name", api_id, api_hash)


def generate_response(prompt):
    try:
        response = co.chat(
            model="command-r",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=50,  # Ограничиваем длину ответа
        )

        print("Полный ответ Cohere:", response)  # 👀 Выводим весь ответ API

        # Правильный способ извлечь текст
        if response.message and response.message.content:
            return response.message.content[0].text.strip()
        else:
            return "Ошибка: API не вернул текст."
    except Exception as e:
        return f"Ошибка при обработке ответа: {str(e)}"


@client.on(events.NewMessage(incoming=True))
async def handle_new_message(event):
    user_message = event.message.message
    sender = await event.get_sender()
    print(f"Новое сообщение от {sender.username}: {user_message}")

    # Логика для записи на просмотр
    if "записаться на просмотр" in user_message.lower():
        await event.reply("Пожалуйста, укажите удобную дату и время для просмотра.")
    elif "дата" in user_message.lower() and "время" in user_message.lower():
        await event.reply("Вы успешно записаны на просмотр!")
    else:
        # Генерируем ответ с помощью Cohere
        prompt = f"Ты риелтор. Тебе пишет клиент, который увидел твое объявление о крартире на церетели, за 350 долларов. Кондиционер есть, спальня одна, кухня отдельно. вид во двор,этаж второй. Возможно тебе понадобится эта информация. Отвечай кратко. в 2-3 предложениях. Отвечай на вопросы клиента. Клиент пишет: {user_message}. Ответь ему."
        response = generate_response(prompt)
        # Отправляем ответ
        await event.reply(response)
        print(f"Ответ отправлен: {response}")


async def main():
    # Авторизация (если сессия уже существует, повторная авторизация не потребуется)
    await client.start()
    print("Авторизация прошла успешно!")

    # Получаем информацию о себе
    me = await client.get_me()
    print(f"Я вошел как: {me.first_name} ({me.username})")

    # Запуск клиента
    await client.run_until_disconnected()


# Запускаем клиент
with client:
    client.loop.run_until_complete(main())
