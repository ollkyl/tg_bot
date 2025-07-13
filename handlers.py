from aiogram import F, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import AiogramError

from keyboards import (
    inline_kb,
    main_menu,
    get_min_price_keyboard,
    get_max_price_keyboard,
    get_count_of_rooms_keyboard,
    get_period_keyboard,
    get_district_keyboard,
    rooms,
    districts,
    finish_messages,
)
from states import Selection, ApartmentForm, BroadcastState
from db import add_client, add_apartment, get_all_users


def register_handlers(dp, bot, ADMIN_ID):
    @dp.message(Command("cancel"))
    async def cmd_cancel(message: types.Message, state: FSMContext):
        await state.clear()
        await message.answer("Операция отменена. Вы можете начать с новой команды.")

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

    # @dp.message(Command("add_apartment"))
    # async def cmd_add_apartment(message: types.Message, state: FSMContext):
    #     if message.from_user.id != ADMIN_ID:
    #         await message.answer("У вас нет прав для выполнения этой команды.")
    #         return
    #     await message.answer(
    #         "Введите данные квартиры в следующем формате СТРОГО ЧЕРЕЗ @:\n\n"
    #         "Агент @ Название @ Цена @ период @ доп. информация @ Район @ комнатность \n\n"
    #         "Пример:\n"
    #         " DBX_real_estate @ Сдается 2-bedroom в Business Bay!@ 180000@ от года@ депозит - 16.500 AED@ The Pad by Omniyat @ 2-комнатная \n\n"
    #         "Для завершения отправьте команду /add_and_send."
    #     )
    #     await state.update_data(file_ids=[], apartment_data=None)
    #     await state.set_state(ApartmentForm.waiting_for_data)

    # @dp.message(StateFilter(ApartmentForm.waiting_for_data), ~Command(commands=["add_and_send"]))
    # async def process_apartment_data(msg: types.Message, state: FSMContext):
    #     current_data = await state.get_data()
    #     file_ids = current_data.get("file_ids", [])
    #     if msg.caption or msg.text:
    #         if msg.caption:
    #             data = [item.strip() for item in msg.caption.split("@")]
    #         else:
    #             data = [item.strip() for item in msg.text.split("@")]
    #         await msg.answer(f"Вы ввели: {data}")
    #         if len(data) < 6:
    #             await msg.answer("Неверный формат. Убедитесь, что вы указали все поля.")
    #             return
    #         if not current_data.get("apartment_data"):
    #             await state.update_data(apartment_data=data)
    #             await msg.answer("Данные квартиры сохранены.")
    #         else:
    #             await msg.answer(
    #                 "Данные квартиры уже введены. Продолжайте отправлять фото или завершите ввод командой /add_and_send."
    #             )
    #     if msg.photo or msg.video:
    #         file_id = msg.photo[-1].file_id if msg.photo else msg.video.file_id
    #         file_ids.append(file_id)
    #         await state.update_data(file_ids=file_ids)
    #         await msg.answer(
    #             "Фото добавлено. Отправьте следующее, если нужно, или завершите командой /add_and_send."
    #         )

    # @dp.message(Command("add_and_send"), StateFilter(ApartmentForm.waiting_for_data))
    # async def cmd_add_and_send(message: types.Message, state: FSMContext):
    #     current_data = await state.get_data()
    #     apartment_data = current_data.get("apartment_data")
    #     file_ids = current_data.get("file_ids", [])
    #     if not apartment_data:
    #         await message.answer("Сначала введите данные квартиры с подписью.")
    #         return
    #     try:
    #         agent, title, price_str, period, info, district = apartment_data[:6]
    #         rooms = apartment_data[6] if len(apartment_data) > 6 else "Не указано"
    #         price = int(price_str)
    #     except Exception as e:
    #         await message.answer("Ошибка при обработке данных квартиры.")
    #         logging.error(f"Ошибка при обработке данных: {e}")
    #         return
    #     apartment_id, matching_clients = await add_apartment(
    #         agent, title, price, rooms, district, period, info, file_ids
    #     )
    #     await message.answer(f"Квартира добавлена с ID {apartment_id}.")
    #     print("matching_clients:", matching_clients)
    #     if matching_clients:
    #         apartment_message = (
    #             f"🏠 {title}\n"
    #             f"💰 Цена: {price} AED\n"
    #             f"🛏️ Комнаты: {rooms}\n"
    #             f"📍 Адрес: {district}\n"
    #             f"⌛ Период: {period}\n"
    #             f"ℹ️ Инфо: {info}\n"
    #             f"Контакт: @{agent}"
    #         )
    #         await message.answer(f"Найдено совпадений по параметрам {len(matching_clients)}.")
    #         sent_usernames = []
    #         for user_id, user_name in matching_clients:
    #             try:
    #                 if user_id is None:
    #                     print("user_id is None!")
    #                 else:
    #                     if user_name:
    #                         sent_usernames.append(user_name)
    #                     else:
    #                         sent_usernames.append("Без имени")
    #                     if file_ids:
    #                         media = []
    #                         for file_id in file_ids:
    #                             if file_id.startswith("AgAC") or file_id.startswith("AgAD"):
    #                                 media.append(types.InputMediaPhoto(media=file_id))
    #                             else:
    #                                 media.append(types.InputMediaVideo(media=file_id))
    #                         if media:
    #                             media[0].caption = apartment_message
    #                         await bot.send_media_group(chat_id=user_id, media=media)
    #                     else:
    #                         await bot.send_photo(user_id, apartment_message)
    #             except AiogramError as e:
    #                 logging.error(f"Не удалось отправить сообщение пользователю {user_id}: {e}")
    #         if sent_usernames:
    #             await message.answer(
    #                 f"Сообщения были отправлены пользователям: {', '.join(sent_usernames)}."
    #             )
    #     else:
    #         await message.answer("Подходящих клиентов не найдено.")
    #     await state.clear()

    @dp.message(Command("start"))
    async def send_welcome(message: types.Message, state: FSMContext):
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

    @dp.callback_query(F.data == "button_period")
    async def choosing_period(callback: types.CallbackQuery, state: FSMContext):
        await callback.message.edit_text(
            "Выберите срок аренды:", reply_markup=get_period_keyboard()
        )
        await state.set_state(Selection.choosing_period)

    @dp.callback_query(F.data.in_(["от года или помесячно", "помесячно"]))
    async def confirm_period_choice(callback: types.CallbackQuery, state: FSMContext):
        period = callback.data
        await state.update_data(period=period)
        await callback.message.edit_text(f"Вы выбрали: {period}")
        await return_to_main_menu(callback, state)

    @dp.callback_query(F.data == "button_district")
    async def choosing_district(callback: types.CallbackQuery, state: FSMContext):
        await callback.message.edit_text(
            "Выберите районы:",
            reply_markup=get_district_keyboard(districts, selected_districts=[]),
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

    @dp.callback_query(F.data == "back")
    async def go_back(callback: types.CallbackQuery, state: FSMContext):
        await callback.message.edit_text("Выберите параметры:", reply_markup=inline_kb)

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
            "<code>📆 Срок аренды:</code> <b>Не выбрано</b>"
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
            await state.clear()
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
        district = ", ".join(districts_selected) if districts_selected else "Не выбрано"
        selected_rooms = data.get("count_of_rooms", [])
        count_of_rooms = ", ".join(selected_rooms) if selected_rooms else "Не выбрано"
        min_price = data.get("min_price", 0)
        max_price = data.get("max_price", 1000000)
        period = data.get("period", "Не выбрано")
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
        save_count += 1
        if save_count == 1:
            message_index = 0
        else:
            message_index = 1 + ((save_count - 2) % 5)
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
        period = data.get("period", "Не выбрано")
        if min_price != "Не выбрано":
            selected_text = (
                f"Выбраные параметры:\n"
                f"<code>🏠 Районы:</code> <b>{district}</b>\n"
                f"<code>💰 Диапазон цены:</code> <b>{min_price} </b> - <b>{max_price} AED в месяц</b>\n"
                f"<code>🛏 Комнаты:</code> <b>{count_of_rooms}</b>\n"
                f"<code>📆 Срок аренды:</code> <b>{period}</b>"
            )
        else:
            selected_text = (
                f"Выбраные параметры:\n"
                f"<code>🏠 Районы:</code> <b>{district}</b>\n"
                f"<code>💰 Диапазон цены:</code> <b>{min_price}</b>\n"
                f"<code>🛏 Комнаты:</code> <b>{count_of_rooms}</b>\n"
                f"<code>📆 Срок аренды:</code> <b>{period}</b>"
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
