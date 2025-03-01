from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import Command
from aiogram.exceptions import AiogramError
import asyncio
import logging
from dotenv import dotenv_values
from db import add_client, add_apartment

env_values = dotenv_values(".env")
API_TOKEN = env_values.get("API_TOKEN")
ADMIN_ID = int(
    env_values.get("ADMIN_ID")
)  # ID администратора, которому разрешено добавлять квартиры

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()


# Определяем состояния для выбора цены
class Selection(StatesGroup):
    choosing_min_price = State()
    choosing_max_price = State()
    choosing_count_of_rooms = State()
    choosing_district = State()
    choosing_period = State()
    selected_message_id = State()
    user_id = State()


# Кнопки главного меню
inline_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Район", callback_data="button_district")],
        [InlineKeyboardButton(text="Цена", callback_data="button_price")],
        [InlineKeyboardButton(text="Комнаты", callback_data="button_rooms")],
        [InlineKeyboardButton(text="Срок аренды", callback_data="button_period")],
        [InlineKeyboardButton(text="Сохранить выбор", callback_data="button_save")],
        [InlineKeyboardButton(text="Отчистить всё", callback_data="button_delete")],
    ]
)


# Кнопки выбора минимальной цены
def get_min_price_keyboard():
    return InlineKeyboardMarkup(
        row_width=2,  # 2 кнопки в ряду
        inline_keyboard=[
            [InlineKeyboardButton(text=str(price), callback_data=f"min_{price}")]
            for price in range(4000, 40000, 2000)
        ]
        + [[InlineKeyboardButton(text="Назад", callback_data="back")]],
    )


# Кнопки выбора максимальной цены (динамически формируются)
def get_max_price_keyboard(min_price):
    return InlineKeyboardMarkup(
        row_width=2,  # 2 кнопки в ряду
        inline_keyboard=[
            [InlineKeyboardButton(text=str(price), callback_data=f"max_{price}")]
            for price in range(min_price + 1000, 40000, 1000)
        ]
        + [[InlineKeyboardButton(text="🔙 Назад", callback_data="back")]],
    )


rooms = ["студия", "1-комнатная", "2-комнатная", "3-комнатная", "4-комнатная"]


# Кнопки выбора комнат
def get_count_of_rooms_keyboard(rooms, selected_rooms):
    buttons = []
    for room in rooms:
        text = f"✅ {room}" if room in selected_rooms else room
        buttons.append([InlineKeyboardButton(text=text, callback_data=room)])

    buttons.append([InlineKeyboardButton(text="Готово", callback_data="room_done")])
    buttons.append([InlineKeyboardButton(text="Назад", callback_data="back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# Кнопки выбора срока
def get_period_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="помесячно", callback_data="помесячно")],
            [InlineKeyboardButton(text="от года", callback_data="от года")],
        ]
        + [[InlineKeyboardButton(text="Назад", callback_data="back")]]
    )


districts = [
    "Downtown Dubai & Business Bay",
    "DIFC & Za'abeel",
    "Dubai Marina & JBR",
    "Palm Jumeirah & Bluewaters Island",
    "Jumeirah (Jumeirah 1, 2, 3, Al Wasl, Al Safa)",
    "Dubai Media City & Dubai Internet City",
    "Dubai Hills Estate & Al Barsha",
    "JVC & JVT",
    "Arjan & Al Furjan",
    "Discovery Gardens & The Gardens",
    "Dubai Sports City & Motor City",
    "Dubai Production City & Dubai Studio City",
    "Meydan (Sobha Hartland, Azizi Riviera)",
    "Dubai Creek Harbour & Dubai Design District",
    "Dubai South & Emaar South",
    "Damac Hills & Damac Hills 2",
    "Al Jaddaf & Dubai Healthcare City (DHCC)",
    "International City & Dubai Silicon Oasis",
]


# Кнопки выбора района
def get_district_keyboard(districts, selected_districts):
    buttons = []
    for district in districts:
        text = f"✅ {district}" if district in selected_districts else district
        buttons.append([InlineKeyboardButton(text=text, callback_data=district)])

    buttons.append([InlineKeyboardButton(text="Готово", callback_data="district_done")])
    buttons.append([InlineKeyboardButton(text="Назад", callback_data="back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# Структура состояний
class ApartmentForm(StatesGroup):
    waiting_for_data = State()


@dp.message(Command("add_apartment"))
async def cmd_add_apartment(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("У вас нет прав для выполнения этой команды.")
        return
    await message.answer(
        "Введите данные квартиры в следующем формате:\n\n"
        "Владелец, Название, Цена, Адрес, Доп. информация, Фото (пути через запятую)\n\n"
        "Пример:\n"
        "Иван Иванов, первая хатка,  100000, от года, 2-комнатная, JVC & JVT, Уютная квартира с ремонтом "
    )

    @dp.message()
    async def process_apartment_data(msg: types.Message):
        try:
            # Разбиваем строку по запятым и убираем лишние пробелы
            data = [item.strip() for item in msg.text.split(",")]
            if len(data) < 6:
                await msg.answer("Неверный формат. Убедитесь, что вы указали все поля.")
                return

            owner, title, price_str, period, info, district, rooms = data[:7]

            price = int(price_str)

            apartment_id, matching_clients = await add_apartment(
                owner, title, price, rooms, district, period, info
            )
            await msg.answer(f"Квартира добавлена с ID {apartment_id}.")

            # Отправляем уведомления подходящим клиентам
            if matching_clients:
                apartment_message = (
                    f"🔔 Новое предложение!\n"
                    f"🏠 {title}\n"
                    f"💰 Цена: {price} AED\n"
                    f"📍 Адрес: {district}\n"
                    f"ℹ️ Инфо: {info}"
                )
                for user_id in matching_clients:
                    try:
                        await bot.send_message(user_id, apartment_message)
                    except AiogramError as e:
                        logging.error(
                            f"Не удалось отправить сообщение пользователю {user_id}: {e}"
                        )
            else:
                await msg.answer("Подходящих клиентов не найдено.")

        except Exception as e:
            await msg.answer(
                "Произошла ошибка при добавлении квартиры. Попробуйте снова."
            )
            logging.error(f"Ошибка при добавлении квартиры: {e}")


# Обработчик команды /start
@dp.message(Command("start"))
async def send_welcome(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "👋 Здравствуйте! Я ваш помощник по поиску квартир в аренду.\n\n✅ Укажите желаемые параметры и я буду следить за новыми предложениями. \n\n🆕 Как только появятся квартиры, соответствующие вашим критериям, я отправлю вам информацию! 🚀"
    )
    user_id = message.from_user.id
    user_name = message.from_user.username
    await state.update_data(user_id=user_id)
    await state.update_data(user_name=user_name)
    await message.answer("Выберите параметры:", reply_markup=inline_kb)


# Обработка выбора "Цена"
@dp.callback_query(F.data == "button_price")
async def choose_min_price(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Выберите минимальную цену \n(тысяч AED в месяц):",
        reply_markup=get_min_price_keyboard(),
    )
    await state.set_state(Selection.choosing_min_price)


# Обработка выбора минимальной цены
@dp.callback_query(F.data.startswith("min_"))
async def choose_max_price(callback: types.CallbackQuery, state: FSMContext):
    min_price = int(callback.data.split("_")[1])
    await state.update_data(min_price=min_price)

    await callback.message.edit_text(
        f"Минимальная цена: {min_price}\nТеперь выберите максимальную цену:",
        reply_markup=get_max_price_keyboard(min_price),
    )
    await state.set_state(Selection.choosing_max_price)


# Обработка выбора максимальной цены
@dp.callback_query(F.data.startswith("max_"))
async def confirm_price(callback: types.CallbackQuery, state: FSMContext):
    max_price = int(callback.data.split("_")[1])
    await state.update_data(max_price=max_price)
    await return_to_main_menu(callback, state)


# Обработка выбора количества комнат
@dp.callback_query(F.data == "button_rooms")
async def choosing_count_of_rooms(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Выберите количество комнат:",
        reply_markup=get_count_of_rooms_keyboard(rooms, selected_rooms=[]),
    )
    await state.set_state(Selection.choosing_count_of_rooms)


@dp.callback_query(F.data.in_(rooms))
async def confirm_room_choice(callback: types.CallbackQuery, state: FSMContext):
    room = callback.data
    data = await state.get_data()
    selected_rooms = data.get("count_of_rooms", [])
    if room in selected_rooms:
        selected_rooms.remove(room)
    else:
        selected_rooms.append(room)

    await state.update_data(count_of_rooms=selected_rooms)
    await callback.message.edit_text(
        "Выберите комнаты:",
        reply_markup=get_count_of_rooms_keyboard(rooms, selected_rooms),
    )


@dp.callback_query(F.data == "room_done")
async def confirm_rooms(callback: types.CallbackQuery, state: FSMContext):
    await return_to_main_menu(callback, state)


# Обработка выбора срока


@dp.callback_query(F.data == "button_period")
async def choosing_period(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Выберите срок аренды:", reply_markup=get_period_keyboard()
    )
    await state.set_state(Selection.choosing_period)


@dp.callback_query(F.data.in_(["от года", "помесячно"]))
async def confirm_period_choice(callback: types.CallbackQuery, state: FSMContext):
    period = callback.data

    await state.update_data(period=period)
    await callback.message.edit_text(f"Вы выбрали: {period}")

    await return_to_main_menu(callback, state)


# Обработка выбора района
@dp.callback_query(F.data == "button_district")
async def choosing_district(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Выберите районы:",
        reply_markup=get_district_keyboard(districts, selected_districts=[]),
    )
    await state.set_state(Selection.choosing_district)


# Обработка выбора конкретного района
@dp.callback_query(F.data.in_(districts))  # Обрабатываем кнопки
async def confirm_district(callback: types.CallbackQuery, state: FSMContext):
    district = callback.data
    data = await state.get_data()
    selected_districts = data.get("districts", [])

    if district in selected_districts:
        selected_districts.remove(district)  # Убираем, если уже выбрано
    else:
        selected_districts.append(district)  # Добавляем в список

    await state.update_data(districts=selected_districts)
    await callback.message.edit_text(
        "Выберите район:",
        reply_markup=get_district_keyboard(districts, selected_districts),
    )


@dp.callback_query(F.data == "district_done")
async def confirm_districts(callback: types.CallbackQuery, state: FSMContext):
    await return_to_main_menu(callback, state)


# Обработка кнопки "Назад"
@dp.callback_query(F.data == "back")
async def go_back(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Выберите параметры:", reply_markup=inline_kb)


# Обработка кнопки "Отчистить всё"
@dp.callback_query(F.data == "button_delete")
async def delete_data(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user_id = data.get("user_id")
    user_name = data.get("user_name")
    selected_message_id = data.get("selected_message_id")
    finish_message_id = data.get("finish_message_id")
    save_count = data.get("save_count", 0)

    selected_text = (
        "Выбранные параметры:\n"
        "<code>🏠 Районы:</code> <b>Не выбрано</b>\n"
        "<code>💰 Диапазон цены:</code> <b>Не выбрано</b>\n"
        "<code>🛏 Комнаты:</code> <b>Не выбрано</b>\n"
        "<code>📆 Срок аренды:</code> <b>Не выбрано</b>"
    )

    message_id = data.get("selected_message_id")
    await state.clear()
    if message_id:
        # Если сообщение уже есть, обновляем его
        await bot.edit_message_text(
            selected_text,
            chat_id=callback.message.chat.id,
            message_id=message_id,
            parse_mode="HTML",
        )
        await state.clear()
        # Обновляем состояние, оставляя только user_id и user_name, td
        await state.update_data(
            user_id=user_id,
            user_name=user_name,
            selected_message_id=selected_message_id,
            finish_message_id=finish_message_id,
            save_count=save_count,
        )
    # await return_to_main_menu(callback, state)


# Обработка сохранения данных в БД
@dp.callback_query(F.data == "button_save")
async def save_data(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()

    districts_selected = data.get("districts", [])
    district = ", ".join(districts_selected) if districts_selected else "Не выбрано"

    selected_rooms = data.get("count_of_rooms", [])
    count_of_rooms = ", ".join(selected_rooms) if selected_rooms else "Не выбрано"

    min_price = data.get("min_price", None)
    max_price = data.get("max_price", None)
    period = data.get("period", "Не выбранно")
    user_id = data.get("user_id")
    user_name = data.get("user_name")
    save_count = data.get("save_count", 0)
    await add_client(
        user_id,
        min_price,
        max_price,
        count_of_rooms,
        district,
        period,
        user_name,
    )
    await callback.answer("Данные сохранены!")
    finish_messages = [
        "Параметры сохранены! Мы уведомим вас, как только появится подходящее объявление.",
        "Параметры обновлены. Мы сообщим вам, как только найдётся квартира по вашим критериям.",
        "Ваши параметры обновлены! Оповестим вас, как только появятся новые подходящие варианты.",
        "Настройки поиска обновлены. Вы получите уведомление, как только появится квартира по вашим параметрам.",
        "Параметры успешно обновлены! Мы сообщим вам о новых подходящих объявлениях.",
        "Ваши параметры обновлены. Теперь мы ищем квартиру по актуальным настройкам и уведомим вас при появлении подходящего варианта.",
    ]

    save_count += 1

    if save_count == 1:
        message_index = 0
    else:
        message_index = 1 + ((save_count - 2) % 5)

    finish_message_id = data.get("finish_message_id")
    finish_message = finish_messages[message_index]
    try:
        if finish_message_id:
            # Если сообщение уже есть, обновляем его
            await bot.edit_message_text(
                text=finish_message,
                chat_id=callback.message.chat.id,
                message_id=finish_message_id,
                parse_mode="HTML",
            )
        else:
            # Если сообщения нет, отправляем новое и сохраняем его ID
            sent_message = await callback.message.answer(
                finish_message, parse_mode="HTML"
            )
            await state.update_data(finish_message_id=sent_message.message_id)
        await state.update_data(save_count=save_count)
    except AiogramError as e:
        if "message is not modified" in str(e):
            # Логируем, но не прерываем выполнение, если текст не изменился
            logging.info(f"Сообщение не было изменено: {finish_message}")
        else:
            # Если другая ошибка Telegram, отправляем новое сообщение
            logging.error(f"Ошибка Telegram при редактировании сообщения: {e}")
            sent_message = await callback.message.answer(
                finish_message, parse_mode="HTML"
            )
            await state.update_data(confirmation_message_id=sent_message.message_id)


async def return_to_main_menu(callback: types.CallbackQuery, state: FSMContext):
    """Обновляет сообщение с выбранными параметрами."""
    data = await state.get_data()

    districts_selected = data.get("districts", [])
    district = ", ".join(districts_selected) if districts_selected else "Не выбрано"

    selected_rooms = data.get("count_of_rooms", [])
    count_of_rooms = ", ".join(selected_rooms) if selected_rooms else "Не выбрано"

    min_price = data.get("min_price", "Не выбрано")
    max_price = data.get("max_price", "Не выбрано")
    period = data.get("period", "Не выбранно")
    if min_price != "Не выбрано":
        selected_text = (
            f"Выбранные параметры:\n"
            f"<code>🏠 Районы:</code> <b>{district}</b>\n"
            f"<code>💰 Диапазон цены:</code> <b>{min_price} k </b> - <b>{max_price} k AED </b>\n"
            f"<code>🛏 Комнаты:</code> <b>{count_of_rooms}</b>\n"
            f"<code>📆 Срок аренды:</code> <b>{period}</b>"
        )
    else:
        selected_text = (
            f"Выбранные параметры:\n"
            f"<code>🏠 Районы:</code> <b>{district}</b>\n"
            f"<code>💰 Диапазон цены:</code> <b>{min_price}</b>\n"
            f"<code>🛏 Комнаты:</code> <b>{count_of_rooms}</b>\n"
            f"<code>📆 Срок аренды:</code> <b>{period}</b>"
        )
    message_id = data.get("selected_message_id")
    try:
        if message_id:
            # Если сообщение уже есть, обновляем его
            await bot.edit_message_text(
                selected_text,
                chat_id=callback.message.chat.id,
                message_id=message_id,
                parse_mode="HTML",
            )
        else:
            # Если сообщения нет, отправляем новое и сохраняем его ID
            sent_message = await callback.message.answer(
                selected_text, parse_mode="HTML"
            )
            await state.update_data(selected_message_id=sent_message.message_id)

    except AiogramError as e:
        if "message is not modified" in str(e):
            logging.warning("Сообщение не изменилось.")
        else:
            logging.error(f"Ошибка при редактировании сообщения: {e}")
            raise

    await callback.message.edit_text("Выберите параметр:", reply_markup=inline_kb)


# Запуск бота
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
