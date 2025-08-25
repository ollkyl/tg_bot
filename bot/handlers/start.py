from aiogram import types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from bot.keyboards import main_menu, inline_kb
from db import add_subscription, create_database_engine_and_session

# Global database engine and session for main thread
db_engine = None
async_session = None


async def init_main_db():
    """Initialize database engine and session for main thread."""
    global db_engine, async_session
    db_engine, async_session = create_database_engine_and_session()


period_translations = {
    "monthly": "помесячно",
    "daily": "посуточно",
    "yearly": "от года",
}

furnishing_translations = {
    "furnished": "Меблированная",
    "unfurnished": "Немеблированная",
}

rooms_translation = {
    "студия": "100",
    "1-комнатная": "1",
    "2-комнатная": "2",
    "3-комнатная": "3",
    "4-комнатная": "4",
}

subscription_translations = {
    "day": "день",
    "week": "неделю",
    "month": "месяц",
}


def get_selected_text(data):
    districts = ", ".join(data.get("districts", [])) or "Не выбрано"
    reverse_rooms_translation = {v: k for k, v in rooms_translation.items()}
    rooms = (
        ", ".join(reverse_rooms_translation.get(r, r) for r in data.get("count_of_rooms", []))
        or "Не выбрано"
    )
    min_price = data.get("min_price", "Не выбрано")
    max_price = data.get("max_price", "Не выбрано")
    period = (
        ", ".join(period_translations.get(p, p) for p in data.get("periods", [])) or "Не выбрано"
    )
    furnishing = (
        ", ".join(furnishing_translations.get(f, f) for f in data.get("furnishing", []))
        or "Не выбрано"
    )

    return (
        f"Выбраные параметры:\n"
        f"<code>🏠 Районы:</code> <b>{districts}</b>\n"
        f"<code>💰 Диапазон цены:</code> <b>{min_price} - {max_price} AED в месяц</b>\n"
        f"<code>🛏 Комнаты:</code> <b>{rooms}</b>\n"
        f"<code>📆 Срок аренды:</code> <b>{period}</b>\n"
        f"<code>🪑 Меблировка:</code> <b>{furnishing}</b>"
    )


async def update_selected_message(callback: types.CallbackQuery, state: FSMContext, bot):
    data = await state.get_data()
    selected_text = get_selected_text(data)
    selected_message_id = data.get("selected_message_id")
    try:
        if selected_message_id:
            await bot.edit_message_text(
                text=selected_text,
                chat_id=callback.message.chat.id,
                message_id=selected_message_id,
                parse_mode="HTML",
            )
        else:
            msg = await callback.message.answer(selected_text, parse_mode="HTML")
            await state.update_data(selected_message_id=msg.message_id)
    except Exception:
        print("Ошибка при обновлении сообщения с выбранными параметрами.")


def register_start(dp, bot):
    @dp.message(Command("start"))
    async def send_welcome(message: types.Message, state: FSMContext):
        await state.clear()
        user_id = message.from_user.id
        user_name = message.from_user.username

        await state.update_data(user_id=user_id, user_name=user_name, save_count=0)

        await message.answer(
            "👋 Добро пожаловать! Я — ваш помощник по аренде квартир в Дубае.\n\n"
            "📢 Все новые объявления появляются в нашем канале: t.me/apartDubaiApart .\n\n"
            "✅ Укажите параметры, которые вас интересуют — и я буду присылать вам подходящие варианты, как только они появятся.",
            reply_markup=main_menu,
        )

        menu_message = await message.answer("Выберите параметры:", reply_markup=inline_kb)
        selected_text = get_selected_text({})
        params_message = await message.answer(selected_text, parse_mode="HTML")

        await state.update_data(
            menu_message_id=menu_message.message_id,
            selected_message_id=params_message.message_id,
            selected_text=selected_text,
            current_menu_text="Выберите параметры:",
        )

        data = await state.get_data()
        print(f"🔍 FSM: {await state.get_state()} | DATA: { {k: v for k, v in data.items()} }")

    @dp.message(Command("cancel"))
    async def cmd_cancel(message: types.Message, state: FSMContext):
        await state.clear()
        await message.answer("Операция отменена.")

    @dp.message(Command("weawer"))
    async def cmd_weawer(message: types.Message, state: FSMContext):
        user_id = message.from_user.id
        async with async_session() as session:
            await add_subscription(user_id=user_id, subscription_type="day", session=session)
        await state.update_data(subscription_type="day", subscription_active=True)
        await message.answer(
            f"Доступ к боту на {subscription_translations['day']} активирован!",
            reply_markup=inline_kb,
        )

    @dp.message(F.text == "Вызвать меню")
    async def call_menu(message: types.Message, state: FSMContext):
        data = await state.get_data()
        print(f"🔍 FSM: {await state.get_state()} | DATA: { {k: v for k, v in data.items()} }")

        # Удаляем старые сообщения
        for msg_key in [
            "selected_message_id",
            "subscription_message_id",
            "invoice_message_id",
            "finish_message_id",
        ]:
            msg_id = data.get(msg_key)
            if msg_id:
                try:
                    await message.bot.delete_message(chat_id=message.chat.id, message_id=msg_id)
                except Exception:
                    pass

        # Обновляем параметры, если вдруг они не заданы
        user_id = data.get("user_id") or message.from_user.id
        user_name = data.get("user_name") or message.from_user.username

        # Показываем меню и параметры
        menu_message = await message.answer("Выберите параметры:", reply_markup=inline_kb)
        selected_text = get_selected_text(data)
        params_message = await message.answer(selected_text, parse_mode="HTML")

        # Обновляем состояние
        await state.update_data(
            user_id=user_id,
            user_name=user_name,
            menu_message_id=menu_message.message_id,
            selected_message_id=params_message.message_id,
            selected_text=selected_text,
            subscription_message_id=None,
            invoice_message_id=None,
            finish_message_id=None,
            current_menu_text="Выберите параметры:",
        )
