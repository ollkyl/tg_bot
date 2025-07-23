from aiogram import types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from bot.keyboards import main_menu, inline_kb
from db import add_subscription

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

subscription_translations = {"day": "день", "week": "неделю", "month": "месяц"}


def get_selected_text(data):
    districts = ", ".join(data.get("districts", [])) or "Не выбрано"
    rooms = ", ".join(data.get("count_of_rooms", [])) or "Не выбрано"
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


def register_start(dp, bot):
    @dp.message(Command("start"))
    async def send_welcome(message: types.Message, state: FSMContext):
        await state.clear()
        user_id = message.from_user.id
        user_name = message.from_user.username
        await state.update_data(user_id=user_id, user_name=user_name)
        await message.answer(
            "👋 Здравствуйте! Я ваш помощник по поиску квартир в аренду.\n\n"
            "✅ Укажите желаемые параметры и я буду следить за новыми предложениями.",
            reply_markup=main_menu,
        )
        menu_message = await message.answer("Выберите параметры:", reply_markup=inline_kb)
        selected_text = get_selected_text({}, period_translations, furnishing_translations)
        params_message = await message.answer(selected_text, parse_mode="HTML")
        await state.update_data(
            menu_message_id=menu_message.message_id,
            selected_message_id=params_message.message_id,
            selected_text=selected_text,
        )

    @dp.message(Command("cancel"))
    async def cmd_cancel(message: types.Message, state: FSMContext):
        await state.clear()
        await message.answer("Операция отменена.")

    @dp.message(Command("weawer"))
    async def cmd_weawer(message: types.Message, state: FSMContext):
        user_id = message.from_user.id
        await add_subscription(user_id=user_id, subscription_type="day")
        await state.update_data(subscription_type="day", subscription_active=True)
        await message.answer(
            f"Доступ к боту на {subscription_translations['day']} активирован!",
            reply_markup=inline_kb,
        )
