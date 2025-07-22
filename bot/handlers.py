from aiogram import F, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import AiogramError
from bot.keyboards import (
    inline_kb,
    main_menu,
    get_min_price_keyboard,
    get_max_price_keyboard,
    get_count_of_rooms_keyboard,
    get_period_keyboard,
    get_district_keyboard,
    get_furnishing_keyboard,
    get_subscription_keyboard,
    rooms,
    districts,
    finish_messages,
)
from bot.states import Selection, BroadcastState, SubscriptionState
from db import add_client, get_all_users, check_subscription, add_subscription
from datetime import datetime, timedelta

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


def register_handlers(dp, bot, ADMIN_ID):
    @dp.message(Command("cancel"))
    async def cmd_cancel(message: types.Message, state: FSMContext):
        await state.clear()
        await message.answer("Операция отменена. Вы можете начать с новой команды.")

    @dp.message(Command("weawer"))
    async def cmd_weawer(message: types.Message, state: FSMContext):
        print(f"Получена команда /weawer от user_id={message.from_user.id}")
        user_id = message.from_user.id
        await add_subscription(user_id=user_id, subscription_type="day")
        await message.answer("Доступ к боту на день активирован!", reply_markup=main_menu)

    @dp.message(Command("broadcast"))
    async def cmd_broadcast(message: types.Message, state: FSMContext):
        if message.from_user.id != ADMIN_ID:
            await message.answer("У вас нет прав для использования этой команды.")
            return
        await message.answer("Отправьте сообщение, которое нужно разослать всем пользователям.")
        await state.set_state(BroadcastState.waiting_for_message)

    @dp.message(StateFilter(BroadcastState.waiting_for_message))
    async def handle_broadcast_message(message: types.Message, state: FSMContext):
        broadcast_message = message.text
        users = await get_all_users()
        for user_id in users:
            try:
                await bot.send_message(user_id, broadcast_message)
            except Exception as e:
                print(f"Не удалось отправить сообщение пользователю {user_id}: {e}")
                continue
        await message.answer("Рассылка завершена.")
        await state.finish()

    @dp.message(Command("start"))
    async def send_welcome(message: types.Message, state: FSMContext):
        print(f"Получена команда /start от user_id={message.from_user.id}")
        await state.clear()
        user_id = message.from_user.id
        user_name = message.from_user.username
        await state.update_data(user_id=user_id, user_name=user_name)
        await message.answer(
            "👋 Здравствуйте! Я ваш помощник по поиску квартир в аренду.\n\n✅ Укажите желаемые параметры и я буду следить за новыми предложениями. \n\n🆕 Как только появятся квартиры, соответствующие вашим критериям, я отправлю вам информацию! 🚀",
            reply_markup=main_menu,
        )
        await message.answer("Выберите параметры:", reply_markup=inline_kb)

    @dp.message(F.text == "Начать сначала")
    async def restart_bot(message: types.Message, state: FSMContext):
        await state.clear()
        await send_welcome(message, state)

    @dp.callback_query(F.data == "button_price")
    async def choose_min_price(callback: types.CallbackQuery, state: FSMContext):
        await callback.message.edit_text(
            "Выберите минимальную плату \n(AED в месяц):",
            reply_markup=get_min_price_keyboard(),
        )
        await state.set_state(Selection.choosing_min_price)

    @dp.callback_query(F.data.startswith("min_"))
    async def choose_max_price(callback: types.CallbackQuery, state: FSMContext):
        min_price = int(callback.data.split("_")[1])
        await state.update_data(min_price=min_price)
        await callback.message.edit_text(
            f"Минимальная плата: {min_price}\nТеперь выберите максимальную плату:",
            reply_markup=get_max_price_keyboard(min_price),
        )
        await state.set_state(Selection.choosing_max_price)

    @dp.callback_query(F.data.startswith("max_"))
    async def confirm_price(callback: types.CallbackQuery, state: FSMContext):
        max_price = int(callback.data.split("_")[1])
        await state.update_data(max_price=max_price)
        await return_to_main_menu(callback, state)

    @dp.callback_query(F.data == "button_rooms")
    async def choosing_count_of_rooms(callback: types.CallbackQuery, state: FSMContext):
        data = await state.get_data()
        selected_rooms = data.get("count_of_rooms", [])
        await callback.message.edit_text(
            "Выберите количество комнат:",
            reply_markup=get_count_of_rooms_keyboard(rooms, selected_rooms=selected_rooms),
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

    period_options = ["monthly", "daily", "yearly"]

    @dp.callback_query(F.data == "button_period")
    async def choosing_period(callback: types.CallbackQuery, state: FSMContext):
        data = await state.get_data()
        selected_periods = data.get("periods", [])
        await callback.message.edit_text(
            "Выберите срок аренды:",
            reply_markup=get_period_keyboard(selected_periods=selected_periods),
        )
        await state.set_state(Selection.choosing_period)

    @dp.callback_query(F.data.in_(period_options))
    async def confirm_period_choice(callback: types.CallbackQuery, state: FSMContext):
        period = callback.data
        data = await state.get_data()
        selected_periods = data.get("periods", [])
        if period in selected_periods:
            selected_periods.remove(period)
        else:
            selected_periods.append(period)
        await state.update_data(periods=selected_periods)
        await callback.message.edit_text(
            "Выберите срок аренды:", reply_markup=get_period_keyboard(selected_periods)
        )

    @dp.callback_query(F.data == "period_done")
    async def finish_period_selection(callback: types.CallbackQuery, state: FSMContext):
        await return_to_main_menu(callback, state)

    @dp.callback_query(F.data == "button_district")
    async def choosing_district(callback: types.CallbackQuery, state: FSMContext):
        data = await state.get_data()
        selected_districts = data.get("districts", [])
        await callback.message.edit_text(
            "Выберите районы:",
            reply_markup=get_district_keyboard(districts, selected_districts=selected_districts),
        )
        await state.set_state(Selection.choosing_district)

    @dp.callback_query(F.data.in_(districts))
    async def confirm_district(callback: types.CallbackQuery, state: FSMContext):
        district = callback.data
        data = await state.get_data()
        selected_districts = data.get("districts", [])
        if district in selected_districts:
            selected_districts.remove(district)
        else:
            selected_districts.append(district)
        await state.update_data(districts=selected_districts)
        await callback.message.edit_text(
            "Выберите район:",
            reply_markup=get_district_keyboard(districts, selected_districts),
        )

    @dp.callback_query(F.data == "district_done")
    async def confirm_districts(callback: types.CallbackQuery, state: FSMContext):
        await return_to_main_menu(callback, state)

    @dp.callback_query(F.data == "button_furnishing")
    async def choosing_furnishing(callback: types.CallbackQuery, state: FSMContext):
        data = await state.get_data()
        selected_furnishing = data.get("furnishing", [])
        await callback.message.edit_text(
            "Выберите тип меблировки:",
            reply_markup=get_furnishing_keyboard(selected_furnishing=selected_furnishing),
        )
        await state.set_state(Selection.choosing_furnishing)

    @dp.callback_query(F.data.in_(["furnished", "unfurnished"]))
    async def confirm_furnishing_choice(callback: types.CallbackQuery, state: FSMContext):
        furnishing = callback.data
        data = await state.get_data()
        selected_furnishing = data.get("furnishing", [])
        if furnishing in selected_furnishing:
            selected_furnishing.remove(furnishing)
        else:
            selected_furnishing.append(furnishing)
        await state.update_data(furnishing=selected_furnishing)
        await callback.message.edit_text(
            "Выберите тип меблировки:",
            reply_markup=get_furnishing_keyboard(selected_furnishing),
        )

    @dp.callback_query(F.data == "furnishing_done")
    async def finish_furnishing_selection(callback: types.CallbackQuery, state: FSMContext):
        await return_to_main_menu(callback, state)

    @dp.callback_query(F.data == "back")
    async def go_back(callback: types.CallbackQuery, state: FSMContext):
        await callback.message.edit_text("Выберите параметры:", reply_markup=inline_kb)

    @dp.callback_query(F.data == "subscription")
    async def show_subscription_menu(callback: types.CallbackQuery, state: FSMContext):
        await callback.message.edit_text(
            "Выберите тип подписки:", reply_markup=get_subscription_keyboard()
        )
        await state.set_state(SubscriptionState.choosing_subscription)

    @dp.callback_query(F.data == "button_delete")
    async def delete_data(callback: types.CallbackQuery, state: FSMContext):
        data = await state.get_data()
        user_id = data.get("user_id")
        user_name = data.get("user_name")
        selected_message_id = data.get("selected_message_id")
        finish_message_id = data.get("finish_message_id")
        save_count = data.get("save_count", 0)
        selected_text = (
            "Выбраные параметры:\n"
            "<code>🏠 Районы:</code> <b>Не выбрано</b>\n"
            "<code>💰 Диапазон цены:</code> <b>Не выбрано</b>\n"
            "<code>🛏 Комнаты:</code> <b>Не выбрано</b>\n"
            "<code>📆 Срок аренды:</code> <b>Не выбрано</b>\n"
            "<code>🪑 Меблировка:</code> <b>Не выбрано</b>"
        )
        message_id = data.get("selected_message_id")
        await state.clear()
        if message_id:
            await bot.edit_message_text(
                selected_text,
                chat_id=callback.message.chat.id,
                message_id=message_id,
                parse_mode="HTML",
            )
            await state.update_data(
                user_id=user_id,
                user_name=user_name,
                selected_message_id=selected_message_id,
                finish_message_id=finish_message_id,
                save_count=save_count,
            )

    @dp.callback_query(F.data == "button_save")
    async def save_data(callback: types.CallbackQuery, state: FSMContext):
        data = await state.get_data()
        districts_selected = data.get("districts", [])
        district = ", ".join(districts_selected) if districts_selected else None
        selected_rooms = data.get("count_of_rooms", [])
        count_of_rooms = (
            ", ".join(rooms_translation.get(room, room) for room in selected_rooms)
            if selected_rooms
            else None
        )
        min_price = data.get("min_price", 0)
        max_price = data.get("max_price", 1000000)
        periods = data.get("periods", [])
        period = ", ".join(periods) if periods else None
        furnishing_list = data.get("furnishing", [])
        furnishing = None
        if len(furnishing_list) == 1:
            furnishing = furnishing_list[0] == "furnished"
        user_id = data.get("user_id")
        user_name = data.get("user_name")
        save_count = data.get("save_count", 0)

        # Проверка подписки
        has_subscription = await check_subscription(user_id)
        if not has_subscription:
            await callback.message.answer(
                "Для получения объявлений оформите подписку через кнопку 'Подписка'.",
                reply_markup=main_menu,
            )
            await callback.answer("Подписка требуется!")
            # Сохраняем параметры, чтобы пользователь мог их использовать после оплаты
            await add_client(
                user_id,
                min_price,
                max_price,
                count_of_rooms,
                district,
                period,
                user_name,
                furnishing,
            )
            return

        await add_client(
            user_id,
            min_price,
            max_price,
            count_of_rooms,
            district,
            period,
            user_name,
            furnishing,
        )
        await callback.answer("Данные сохранены!")
        save_count += 1
        message_index = 0 if save_count == 1 else 1 + ((save_count - 2) % 5)
        finish_message_id = data.get("finish_message_id")
        finish_message = finish_messages[message_index]
        try:
            if finish_message_id:
                await bot.edit_message_text(
                    text=finish_message,
                    chat_id=callback.message.chat.id,
                    message_id=finish_message_id,
                    parse_mode="HTML",
                )
            else:
                sent_message = await callback.message.answer(finish_message, parse_mode="HTML")
                await state.update_data(finish_message_id=sent_message.message_id)
            await state.update_data(save_count=save_count)
        except AiogramError as e:
            if "message is not modified" in str(e):
                print(f"Сообщение не было изменено: {finish_message}")
            else:
                sent_message = await callback.message.answer(finish_message, parse_mode="HTML")
                await state.update_data(confirmation_message_id=sent_message.message_id)

    async def return_to_main_menu(callback: types.CallbackQuery, state: FSMContext):
        data = await state.get_data()
        districts_selected = data.get("districts", [])
        district = ", ".join(districts_selected) if districts_selected else "Не выбрано"
        selected_rooms = data.get("count_of_rooms", [])
        count_of_rooms = ", ".join(selected_rooms) if selected_rooms else "Не выбрано"
        min_price = data.get("min_price", "Не выбрано")
        max_price = data.get("max_price", "Не выбрано")
        periods = data.get("periods", [])
        period = (
            ", ".join(period_translations.get(p, p) for p in periods) if periods else "Не выбрано"
        )
        furnishing = data.get("furnishing", [])
        furnishing_text = (
            ", ".join(furnishing_translations.get(f, f) for f in furnishing)
            if furnishing
            else "Не выбрано"
        )
        selected_text = (
            f"Выбраные параметры:\n"
            f"<code>🏠 Районы:</code> <b>{district}</b>\n"
            f"<code>💰 Диапазон цены:</code> <b>{min_price} - {max_price} AED в месяц</b>\n"
            f"<code>🛏 Комнаты:</code> <b>{count_of_rooms}</b>\n"
            f"<code>📆 Срок аренды:</code> <b>{period}</b>\n"
            f"<code>🪑 Меблировка:</code> <b>{furnishing_text}</b>"
        )
        message_id = data.get("selected_message_id")
        try:
            if message_id:
                await bot.edit_message_text(
                    selected_text,
                    chat_id=callback.message.chat.id,
                    message_id=message_id,
                    parse_mode="HTML",
                )
            else:
                sent_message = await callback.message.answer(selected_text, parse_mode="HTML")
                await state.update_data(selected_message_id=sent_message.message_id)
        except AiogramError as e:
            if "message is not modified" in str(e):
                print("Сообщение не изменилось.")
            else:
                print(f"Ошибка при редактировании сообщения: {e}")
                raise
        await callback.message.edit_text("Выберите параметр:", reply_markup=inline_kb)
