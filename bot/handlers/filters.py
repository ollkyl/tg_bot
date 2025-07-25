from aiogram import types, F
from aiogram.fsm.context import FSMContext
from bot.keyboards import (
    get_min_price_keyboard,
    get_max_price_keyboard,
    get_count_of_rooms_keyboard,
    get_period_keyboard,
    get_district_keyboard,
    get_furnishing_keyboard,
    inline_kb,
    rooms,
    districts,
)
from bot.states import Selection
from bot.handlers.start import update_selected_message


async def return_to_main_menu(callback: types.CallbackQuery, state: FSMContext, bot):
    await update_selected_message(callback, state, bot)
    await callback.message.edit_text("Выберите параметры:", reply_markup=inline_kb)
    await state.set_state(None)
    await callback.answer()


def register_filters(dp, bot):
    @dp.callback_query(F.data == "button_price")
    async def choose_min_price(callback: types.CallbackQuery, state: FSMContext):
        await callback.message.edit_text(
            "Выберите минимальную плату \n(AED в месяц):", reply_markup=get_min_price_keyboard()
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
        await return_to_main_menu(callback, state, bot)

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
            "Выберите комнаты:", reply_markup=get_count_of_rooms_keyboard(rooms, selected_rooms)
        )

    @dp.callback_query(F.data == "room_done")
    async def confirm_rooms(callback: types.CallbackQuery, state: FSMContext):
        await return_to_main_menu(callback, state, bot)

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
        await return_to_main_menu(callback, state, bot)

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
            "Выберите район:", reply_markup=get_district_keyboard(districts, selected_districts)
        )

    @dp.callback_query(F.data == "district_done")
    async def confirm_districts(callback: types.CallbackQuery, state: FSMContext):
        await return_to_main_menu(callback, state, bot)

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
            "Выберите тип меблировки:", reply_markup=get_furnishing_keyboard(selected_furnishing)
        )

    @dp.callback_query(F.data == "furnishing_done")
    async def finish_furnishing_selection(callback: types.CallbackQuery, state: FSMContext):
        await return_to_main_menu(callback, state, bot)

    @dp.callback_query(F.data == "back")
    async def go_back(callback: types.CallbackQuery, state: FSMContext):
        await return_to_main_menu(callback, state, bot)

    @dp.callback_query(F.data == "back_to_main")
    async def back_to_main_menu(callback: types.CallbackQuery, state: FSMContext):
        await update_selected_message(callback, state, bot)
        await callback.message.edit_text("Выберите параметры:", reply_markup=inline_kb)
        await state.update_data(subscription_message_id=None, invoice_message_id=None)
        await state.set_state(None)
        await callback.answer()
