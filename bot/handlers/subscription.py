from aiogram import types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import LabeledPrice, InlineKeyboardMarkup, InlineKeyboardButton
from bot.keyboards import get_subscription_keyboard, inline_kb
from bot.states import SubscriptionState
from db import add_subscription
from bot.handlers.start import (
    subscription_translations,
)


def register_subscription(dp, bot):
    @dp.callback_query(F.data == "subscription")
    async def show_subscription_menu(callback: types.CallbackQuery, state: FSMContext):
        await callback.message.edit_text(
            "Выберите тип подписки:", reply_markup=get_subscription_keyboard()
        )
        await state.set_state(SubscriptionState.choosing_subscription)
        await callback.answer()

    @dp.callback_query(F.data == "back_to_subscription")
    async def back_to_subscription(callback: types.CallbackQuery, state: FSMContext):
        data = await state.get_data()
        invoice_message_id = data.get("invoice_message_id")
        if invoice_message_id:
            try:
                await bot.delete_message(
                    chat_id=callback.message.chat.id, message_id=invoice_message_id
                )
            except Exception as e:
                print(f"Ошибка удаления инвойса: {e}")

        await callback.message.edit_text(
            "Выберите тип подписки:", reply_markup=get_subscription_keyboard()
        )
        await state.update_data(invoice_message_id=None)
        await state.set_state(SubscriptionState.choosing_subscription)
        await callback.answer()

    @dp.callback_query(F.data.in_(["day", "week", "month"]))
    async def process_subscription_choice(callback: types.CallbackQuery, state: FSMContext):
        subscription_type = callback.data
        prices = {
            "day": [LabeledPrice(label="Подписка на день", amount=20)],
            "week": [LabeledPrice(label="Подписка на неделю", amount=50)],
            "month": [LabeledPrice(label="Подписка на месяц", amount=200)],
        }
        data = await state.get_data()
        invoice_message_id = data.get("invoice_message_id")
        if invoice_message_id:
            try:
                await bot.delete_message(
                    chat_id=callback.message.chat.id, message_id=invoice_message_id
                )
            except Exception as e:
                print(f"Ошибка удаления инвойса: {e}")
        await state.update_data(subscription_type=subscription_type)

        pay_button = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Оплатить", pay=True)],
                [InlineKeyboardButton(text="Назад", callback_data="back_to_subscription")],
            ]
        )
        invoice_message = await bot.send_invoice(
            chat_id=callback.message.chat.id,
            title=f"Подписка на {subscription_translations.get(subscription_type, subscription_type)}",
            description=f"Доступ к боту на {subscription_translations.get(subscription_type, subscription_type)}",
            payload=f"{subscription_type}_subscription",
            provider_token="",
            currency="XTR",
            prices=prices[subscription_type],
            start_parameter="subscription",
            reply_markup=pay_button,
        )
        await state.update_data(invoice_message_id=invoice_message.message_id)
        await callback.message.edit_text("Выберите параметры:", reply_markup=inline_kb)
        await callback.answer()

    @dp.pre_checkout_query()
    async def process_pre_checkout_query(pre_checkout_query: types.PreCheckoutQuery):
        await pre_checkout_query.answer(ok=True)

    @dp.message(F.successful_payment)
    async def process_successful_payment(message: types.Message, state: FSMContext):
        data = await state.get_data()
        subscription_type = data.get("subscription_type")
        invoice_message_id = data.get("invoice_message_id")
        subscription_message_id = data.get("subscription_message_id")

        # Удаляем сообщение с ценами (подписки) и инвойс
        for msg_id in [invoice_message_id, subscription_message_id]:
            if msg_id:
                try:
                    await bot.delete_message(chat_id=message.chat.id, message_id=msg_id)
                except Exception as e:
                    print(f"Ошибка удаления сообщения (ID {msg_id}): {e}")
        print(f"uuuuuuuuuupricess {message.from_user.id}")
        await add_subscription(user_id=message.from_user.id, subscription_type=subscription_type)
        await state.update_data(invoice_message_id=None, subscription_message_id=None)
        print(f"uuuuuuuuuuupdate_data {state.get_data}")
        # Отправляем только сообщение об успешной оплате
        await message.answer(
            f"Оплата прошла успешно! Доступ к боту на {subscription_translations.get(subscription_type, subscription_type)} активирован!",
        )
