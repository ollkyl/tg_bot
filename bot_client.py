from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import Command
import asyncio
import logging
from dotenv import dotenv_values

env_values = dotenv_values(".env")
API_TOKEN = env_values.get("API_TOKEN")

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


# Кнопки главного меню
inline_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Район", callback_data="button_district")],
        [InlineKeyboardButton(text="Цена", callback_data="button_price")],
        [InlineKeyboardButton(text="Комнаты", callback_data="button_rooms")],
        [InlineKeyboardButton(text="Срок аренды", callback_data="button_period")],
    ]
)


# Кнопки выбора минимальной цены
def get_min_price_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=str(price), callback_data=f"min_{price}")]
            for price in range(30000, 100000, 10000)
        ]
        + [[InlineKeyboardButton(text="Назад", callback_data="back")]]
    )


# Кнопки выбора максимальной цены (динамически формируются)
def get_max_price_keyboard(min_price):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=str(price), callback_data=f"max_{price}")]
            for price in range(min_price + 10000, 110000, 10000)
        ]
        + [[InlineKeyboardButton(text="Назад", callback_data="back")]]
    )


# Кнопки выбора колличества комнат
def get_count_of_rooms_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="студия", callback_data="студия")],
            [InlineKeyboardButton(text="1-комнатная", callback_data="1-комнатная")],
            [InlineKeyboardButton(text="2-комнатная", callback_data="2-комнатная")],
            [InlineKeyboardButton(text="3-комнатная", callback_data="3-комнатная")],
        ]
        + [[InlineKeyboardButton(text="Назад", callback_data="back")]]
    )


# Кнопки выбора района
def get_district_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Район 1", callback_data="district_1")],
            [InlineKeyboardButton(text="Район 2", callback_data="district_2")],
            [InlineKeyboardButton(text="Район 3", callback_data="district_3")],
            [InlineKeyboardButton(text="Район 4", callback_data="district_4")],
            [InlineKeyboardButton(text="Район 5", callback_data="district_5")],
            [InlineKeyboardButton(text="Район 6", callback_data="district_6")],
            [InlineKeyboardButton(text="Район 7", callback_data="district_7")],
            [InlineKeyboardButton(text="Район 8", callback_data="district_8")],
            [InlineKeyboardButton(text="Район 9", callback_data="district_9")],
            [InlineKeyboardButton(text="Район 10", callback_data="district_10")],
            [InlineKeyboardButton(text="Район 11", callback_data="district_11")],
            [InlineKeyboardButton(text="Район 12", callback_data="district_12")],
            [InlineKeyboardButton(text="Район 13", callback_data="district_13")],
            [InlineKeyboardButton(text="Район 14", callback_data="district_14")],
            [InlineKeyboardButton(text="Район 15", callback_data="district_15")],
            [InlineKeyboardButton(text="Назад", callback_data="back")],
        ]
    )


# Обработчик команды /start
@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    await message.answer("Выберите параметр:", reply_markup=inline_kb)


# Обработка выбора "Цена"
@dp.callback_query(F.data == "button_price")
async def choose_min_price(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Выберите минимальную цену:", reply_markup=get_min_price_keyboard()
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
    data = await state.get_data()
    min_price = data.get("min_price")

    await callback.message.edit_text(f"Вы выбрали диапазон: {min_price} - {max_price}")
    await return_to_main_menu(callback, state)


# Обработка выбора количества комнат
@dp.callback_query(F.data == "button_rooms")
async def choosing_count_of_rooms(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Выберите количество комнат:", reply_markup=get_count_of_rooms_keyboard()
    )
    await state.set_state(Selection.choosing_count_of_rooms)


# Обработка выбора конкретного количества комнат
@dp.callback_query(
    F.data.in_(["студия", "1-комнатная", "2-комнатная", "3-комнатная"])
)  # Обрабатываем кнопки
async def confirm_room_choice(callback: types.CallbackQuery, state: FSMContext):
    count_of_rooms = callback.data  # Получаем количество комнат из callback

    await state.update_data(count_of_rooms=count_of_rooms)  # Сохраняем в FSM
    await callback.message.edit_text(f"Вы выбрали: {count_of_rooms}")  # Подтверждение

    await return_to_main_menu(callback, state)


# Обработка выбора района
@dp.callback_query(F.data == "button_district")
async def choosing_district(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Выберите район:", reply_markup=get_district_keyboard()
    )
    await state.set_state(Selection.choosing_district)


# Обработка выбора конкретного района
@dp.callback_query(
    F.data.in_(
        [
            "district_1",
            "district_2",
            "district_3",
            "district_4",
            "district_5",
            "district_6",
            "district_7",
            "district_8",
            "district_9",
            "district_10",
            "district_11",
            "district_12",
            "district_13",
            "district_14",
            "district_15",
        ]
    )
)  # Обрабатываем кнопки
async def confirm_district(callback: types.CallbackQuery, state: FSMContext):
    district = callback.data

    await state.update_data(district=district)  # Сохраняем в FSM
    await callback.message.reply(f"Вы выбрали: {district}")  # Подтверждение

    await return_to_main_menu(callback, state)


# Обработка кнопки "Назад"
@dp.callback_query(F.data == "back")
async def go_back(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Выберите параметр:", reply_markup=inline_kb)


async def return_to_main_menu(callback: types.CallbackQuery, state: FSMContext):
    """Возвращает пользователя в главное меню после выбора параметра."""
    await callback.message.edit_text("Выберите параметр:", reply_markup=inline_kb)


# Запуск бота
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
