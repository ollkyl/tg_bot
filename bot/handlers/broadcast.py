from aiogram import types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from bot.states import BroadcastState
from db import get_all_users


def register_broadcast(dp, bot, ADMIN_ID):
    @dp.message(Command("broadcast"))
    async def cmd_broadcast(message: types.Message, state: FSMContext):
        if message.from_user.id != ADMIN_ID:
            await message.answer("У вас нет прав для использования этой команды.")
            return
        await message.answer("Отправьте сообщение, которое нужно разослать всем пользователям.")
        await state.set_state(BroadcastState.waiting_for_message)

    @dp.message(StateFilter(BroadcastState.waiting_for_message))
    async def handle_broadcast_message(message: types.Message, state: FSMContext):
        users = await get_all_users()
        for user_id in users:
            try:
                await bot.send_message(user_id, message.text)
            except Exception:
                continue
        await message.answer("Рассылка завершена.")
        await state.clear()
