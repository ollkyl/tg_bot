from aiogram import types, F
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import AiogramError
from bot.keyboards import inline_kb, main_menu, finish_messages
from db import add_client, check_subscription
from bot.handlers.start import (
    get_selected_text,
    rooms_translation,
)


async def update_selected_message(callback: types.CallbackQuery, state: FSMContext, bot):
    data = await state.get_data()
    selected_text = get_selected_text(data)
    selected_message_id = data.get("selected_message_id")

    if selected_message_id:
        try:
            await bot.edit_message_text(
                text=selected_text,
                chat_id=callback.message.chat.id,
                message_id=selected_message_id,
                parse_mode="HTML",
            )
        except Exception:
            pass  # не создаём новое сообщение, просто игнорируем


def register_save_delete(dp, bot):
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
        furnishing = None if len(furnishing_list) != 1 else furnishing_list[0] == "furnished"
        user_id = data.get("user_id")
        user_name = data.get("user_name")
        save_count = data.get("save_count", 0)

        has_subscription = await check_subscription(user_id)
        if not has_subscription:
            await callback.message.answer(
                "Для получения объявлений оформите подписку через кнопку 'Подписка'.",
                reply_markup=main_menu,
            )
            await callback.answer("Подписка требуется!")
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
            user_id, min_price, max_price, count_of_rooms, district, period, user_name, furnishing
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

        await update_selected_message(callback, state, bot)
        await callback.message.edit_text("Выберите параметры:", reply_markup=inline_kb)

    @dp.callback_query(F.data == "button_delete")
    async def delete_data(callback: types.CallbackQuery, state: FSMContext):
        data = await state.get_data()
        user_id = data.get("user_id")
        user_name = data.get("user_name")
        selected_message_id = data.get("selected_message_id")
        menu_message_id = data.get("menu_message_id")
        finish_message_id = data.get("finish_message_id")
        save_count = data.get("save_count", 0)
        selected_text = get_selected_text({})
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
        await update_selected_message(callback, state, bot)
        await callback.message.edit_text("Выберите параметры:", reply_markup=inline_kb)
        await callback.answer()
