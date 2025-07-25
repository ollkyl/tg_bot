from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)

districts = [
    "Citywalk",
    "Bluewaters",
    "The Palm Jumeirah",
    "Dubai Marina",
    "Business Bay",
    "Downtown",
    "DIFC",
    "ZAABEL + DHCC",
    "Dubai Media City + Dubai Internet City",
    "JLT",
    "JVC",
    "Meydan: Sobha + Azizi Riviera",
    "Dubai Design District + Al Jaddaf",
    "JVT",
    "Creek Harbour",
    "Dubai Production City + Sport City + Motor City",
    "Al Furjan + Discovery Garden",
    "Al Quoz",
    "Al Barsha + Arjan",
]

rooms = ["студия", "1-комнатная", "2-комнатная", "3-комнатная", "4-комнатная"]

finish_messages = [
    "Параметры сохранены! Мы уведомим вас, как только появится подходящее объявление.",
    "Параметры обновлены. Мы сообщим вам, как только найдётся квартира по вашим критериям.",
    "Ваши параметры обновлены! Оповестим вас, как только появятся новые подходящие варианты.",
    "Настройки поиска обновлены. Вы получите уведомление, как только появится квартира по вашим параметрам.",
    "Параметры успешно обновлены! Мы сообщим вам о новых подходящих объявлениях.",
    "Ваши параметры обновлены. Теперь мы ищем квартиру по актуальным настройкам и уведомим вас при появлении подходящего варианта.",
]

inline_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Район", callback_data="button_district")],
        [InlineKeyboardButton(text="Цена", callback_data="button_price")],
        [InlineKeyboardButton(text="Комнаты", callback_data="button_rooms")],
        [InlineKeyboardButton(text="Срок аренды", callback_data="button_period")],
        [InlineKeyboardButton(text="Меблировка", callback_data="button_furnishing")],
        [InlineKeyboardButton(text="Подписка", callback_data="subscription")],
        [InlineKeyboardButton(text="❕Сохранить выбор❕", callback_data="button_save")],
        [InlineKeyboardButton(text="Отчистить всё", callback_data="button_delete")],
    ]
)

main_menu = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Вызвать меню")]],
    resize_keyboard=True,
)


def get_subscription_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="1 день", callback_data="day")],
            [InlineKeyboardButton(text="1 неделя", callback_data="week")],
            [InlineKeyboardButton(text="1 месяц", callback_data="month")],
            [InlineKeyboardButton(text="Назад", callback_data="back_to_main")],
        ]
    )


def get_min_price_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=str(price), callback_data=f"min_{price}")]
            for price in range(0, 40000, 1000)
        ]
        + [[InlineKeyboardButton(text="Назад", callback_data="back")]],
    )


def get_max_price_keyboard(min_price):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=str(price), callback_data=f"max_{price}")]
            for price in range(min_price + 1000, 40000, 1000)
        ]
        + [[InlineKeyboardButton(text="🔙 Назад", callback_data="back")]],
    )


def get_count_of_rooms_keyboard(rooms, selected_rooms):
    buttons = []
    for room in rooms:
        text = f"✅ {room}" if room in selected_rooms else room
        buttons.append([InlineKeyboardButton(text=text, callback_data=room)])
    buttons.append([InlineKeyboardButton(text="Готово", callback_data="room_done")])
    buttons.append([InlineKeyboardButton(text="Назад", callback_data="back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_period_keyboard(selected_periods):
    options = [
        ("помесячно", "monthly"),
        ("посуточно", "daily"),
        ("от года", "yearly"),
    ]
    buttons = []
    for label, value in options:
        text = f"✅ {label}" if value in selected_periods else label
        buttons.append([InlineKeyboardButton(text=text, callback_data=value)])
    buttons.append([InlineKeyboardButton(text="Готово", callback_data="period_done")])
    buttons.append([InlineKeyboardButton(text="Назад", callback_data="back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_district_keyboard(districts, selected_districts):
    buttons = []
    for district in districts:
        text = f"✅ {district}" if district in selected_districts else district
        buttons.append([InlineKeyboardButton(text=text, callback_data=district)])
    buttons.append([InlineKeyboardButton(text="Готово", callback_data="district_done")])
    buttons.append([InlineKeyboardButton(text="Назад", callback_data="back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_furnishing_keyboard(selected_furnishing):
    options = [
        ("Меблированная", "furnished"),
        ("Немеблированная", "unfurnished"),
    ]
    buttons = []
    for label, value in options:
        text = f"✅ {label}" if value in selected_furnishing else label
        buttons.append([InlineKeyboardButton(text=text, callback_data=value)])
    buttons.append([InlineKeyboardButton(text="Готово", callback_data="furnishing_done")])
    buttons.append([InlineKeyboardButton(text="Назад", callback_data="back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
