from aiogram.fsm.state import StatesGroup, State


class Selection(StatesGroup):
    choosing_min_price = State()
    choosing_max_price = State()
    choosing_count_of_rooms = State()
    choosing_district = State()
    choosing_period = State()
    selected_message_id = State()
    user_id = State()


class BroadcastState(StatesGroup):
    waiting_for_message = State()
