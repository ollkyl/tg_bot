from aiogram import types, F
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import AiogramError
from bot.keyboards import inline_kb, main_menu, finish_messages
from db import add_client, check_subscription, add_subscription
from bot.handlers.start import (
    get_selected_text,
    rooms_translation,
)

reverse_rooms_translation = {v: k for k, v in rooms_translation.items()}


def register_save_delete(dp, bot):
    @dp.callback_query(F.data == "button_save")
    async def save_data(callback: types.CallbackQuery, state: FSMContext):
        data = await state.get_data()
        districts_selected = data.get("districts", [])
        district = ", ".join(districts_selected) if districts_selected else None

        count_of_rooms = data.get("count_of_rooms", [])
        min_price = data.get("min_price", 0)
        max_price = data.get("max_price", 1000000)
        periods = data.get("periods", [])
        period = ", ".join(periods) if periods else None
        furnishing_list = data.get("furnishing", [])
        furnishing = None if len(furnishing_list) != 1 else furnishing_list[0] == "furnished"
        user_id = data.get("user_id") or callback.from_user.id

        user_name = data.get("user_name")
        save_count = data.get("save_count", 0)

        subscription = await check_subscription(user_id)

        if subscription is None:
            await add_subscription(user_id=user_id, subscription_type="day")
            await callback.message.answer(
                "📢 ДЕЙСТВУЕТ ПРОБНАЯ ПОДПИСКА НА 1 ДЕНЬ",
                reply_markup=main_menu,
                parse_mode="HTML",
            )
        elif subscription == "execute":
            # Сохраняем данные, даже если подписка истекла
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

            await callback.message.answer(
                "📢 <b>Необходима подписка для получения объявлений:</b>\n"
                "▫️ <i>1 день</i> - <b>20</b>⭐   (40 рублей / 1.68 AED)\n"
                "▫️ <i>неделя</i> - <b>50</b>⭐   (90 рублей / 4.2 AED)\n"
                "▫️ <i>месяц</i> - <b>200</b>⭐   (360 рублей / 16.8 AED)\n\n",
                reply_markup=main_menu,
                parse_mode="HTML",
            )
            await callback.answer("Сохранено, но подписка не активна.")
            return
        elif subscription == "active":
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
            except AiogramError:
                sent_message = await callback.message.answer(finish_message, parse_mode="HTML")
                await state.update_data(finish_message_id=sent_message.message_id)

            # Обновление сообщения с параметрами
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
                    sent_message = await callback.message.answer(selected_text, parse_mode="HTML")
                    await state.update_data(selected_message_id=sent_message.message_id)
            except AiogramError as e:
                if "message is not modified" in str(e):
                    print("Сообщение с параметрами не изменилось.")
                else:
                    sent_message = await callback.message.answer(selected_text, parse_mode="HTML")
                    await state.update_data(selected_message_id=sent_message.message_id)

            current_menu_text = data.get("current_menu_text", "")
            if current_menu_text != "Выберите параметры:":
                try:
                    await callback.message.edit_text("Выберите параметры:", reply_markup=inline_kb)
                    await state.update_data(current_menu_text="Выберите параметры:")
                except AiogramError as e:
                    if "message is not modified" in str(e):
                        print("Меню не изменилось, пропускаем редактирование.")
                    else:
                        raise

    @dp.callback_query(F.data == "button_delete")
    async def delete_data(callback: types.CallbackQuery, state: FSMContext):
        data = await state.get_data()

        user_id = data.get("user_id") or callback.from_user.id

        user_name = data.get("user_name")
        selected_message_id = data.get("selected_message_id")
        menu_message_id = data.get("menu_message_id")
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
        await state.update_data(
            user_id=user_id,
            user_name=user_name,
            selected_message_id=selected_message_id,
            menu_message_id=menu_message_id,
            finish_message_id=finish_message_id,
            save_count=save_count,
            selected_text=selected_text,
            districts=[],
            count_of_rooms=[],
            min_price=None,
            max_price=None,
            periods=[],
            furnishing=[],
        )
        if finish_message_id:
            try:
                await bot.delete_message(
                    chat_id=callback.message.chat.id, message_id=finish_message_id
                )
            except Exception:
                pass
        if selected_message_id:
            try:
                await bot.edit_message_text(
                    text=selected_text,
                    chat_id=callback.message.chat.id,
                    message_id=selected_message_id,
                    parse_mode="HTML",
                )
            except AiogramError as e:
                if "message is not modified" in str(e):
                    print("Сообщение с параметрами не изменилось.")
                else:
                    sent_message = await callback.message.answer(selected_text, parse_mode="HTML")
                    await state.update_data(selected_message_id=sent_message.message_id)
        current_menu_text = data.get("current_menu_text", "")
        if current_menu_text != "Выберите параметры:":
            await callback.message.edit_text("Выберите параметры:", reply_markup=inline_kb)
            await state.update_data(current_menu_text="Выберите параметры:")
        await callback.answer()
