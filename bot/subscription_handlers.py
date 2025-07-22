from aiogram import F, types, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import LabeledPrice, InlineKeyboardMarkup, InlineKeyboardButton
from bot.keyboards import get_subscription_keyboard, inline_kb
from bot.states import SubscriptionState
from db import add_subscription, check_subscription
from datetime import datetime, timedelta

router = Router()

subscription_translations = {"day": "день", "week": "неделю", "month": "месяц"}


@router.message(Command("subscribe"))
async def cmd_subscribe(message: types.Message, state: FSMContext):
    subscription_message = await message.answer(
        "Выберите тип подписки:", reply_markup=get_subscription_keyboard()
    )
    await state.update_data(subscription_menu_id=subscription_message.message_id)
    await state.set_state(SubscriptionState.choosing_subscription)


@router.callback_query(F.data == "back_to_main")
async def back_to_main_menu(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    message_id = data.get("selected_message_id")
    subscription_message_id = data.get("subscription_message_id")
    invoice_message_id = data.get("invoice_message_id")
    if subscription_message_id:
        try:
            await callback.message.bot.delete_message(
                chat_id=callback.message.chat.id, message_id=subscription_message_id
            )
        except Exception as e:
            print(f"Ошибка удаления сообщения перед инвойсом: {e}")
    if invoice_message_id:
        try:
            await callback.message.bot.delete_message(
                chat_id=callback.message.chat.id, message_id=invoice_message_id
            )
        except Exception as e:
            print(f"Ошибка удаления инвойса: {e}")
    if data.get("subscription_menu_id"):
        try:
            await callback.message.bot.delete_message(
                chat_id=callback.message.chat.id, message_id=data.get("subscription_menu_id")
            )
        except Exception as e:
            print(f"Ошибка удаления меню подписки: {e}")
    await callback.message.delete()
    if message_id:
        try:
            await callback.message.bot.edit_message_text(
                text="Выберите параметры:",
                chat_id=callback.message.chat.id,
                message_id=message_id,
                reply_markup=inline_kb,
                parse_mode="HTML",
            )
        except Exception as e:
            print(f"Ошибка редактирования сообщения: {e}")
            await callback.message.answer("Выберите параметры:", reply_markup=inline_kb)
    else:
        await callback.message.answer("Выберите параметры:", reply_markup=inline_kb)
    await state.update_data(
        subscription_message_id=None, invoice_message_id=None, subscription_menu_id=None
    )
    await state.set_state(None)
    await callback.answer()


@router.callback_query(F.data == "back_to_subscription")
async def back_to_subscription(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    subscription_message_id = data.get("subscription_message_id")
    invoice_message_id = data.get("invoice_message_id")
    subscription_menu_id = data.get("subscription_menu_id")
    if subscription_message_id:
        try:
            await callback.message.bot.delete_message(
                chat_id=callback.message.chat.id, message_id=subscription_message_id
            )
        except Exception as e:
            print(f"Ошибка удаления сообщения перед инвойсом: {e}")
    if invoice_message_id:
        try:
            await callback.message.bot.delete_message(
                chat_id=callback.message.chat.id, message_id=invoice_message_id
            )
        except Exception as e:
            print(f"Ошибка удаления инвойса: {e}")
    if subscription_menu_id:
        try:
            await callback.message.bot.edit_message_text(
                text="Выберите тип подписки:",
                chat_id=callback.message.chat.id,
                message_id=subscription_menu_id,
                reply_markup=get_subscription_keyboard(),
            )
        except Exception as e:
            print(f"Ошибка редактирования меню подписки: {e}")
            subscription_message = await callback.message.answer(
                "Выберите тип подписки:", reply_markup=get_subscription_keyboard()
            )
            await state.update_data(subscription_menu_id=subscription_message.message_id)
    else:
        subscription_message = await callback.message.answer(
            "Выберите тип подписки:", reply_markup=get_subscription_keyboard()
        )
        await state.update_data(subscription_menu_id=subscription_message.message_id)
    await state.update_data(subscription_message_id=None, invoice_message_id=None)
    await state.set_state(SubscriptionState.choosing_subscription)
    await callback.answer()


@router.callback_query(F.data.in_(["day", "week", "month"]))
async def process_subscription_choice(callback: types.CallbackQuery, state: FSMContext):
    subscription_type = callback.data
    duration_days = {"day": 1, "week": 7, "month": 30}
    prices = {
        "day": [LabeledPrice(label="Подписка на день", amount=100)],
        "week": [LabeledPrice(label="Подписка на неделю", amount=500)],
        "month": [LabeledPrice(label="Подписка на месяц", amount=1500)],
    }

    # Удаляем старое сообщение перед инвойсом и инвойс, если они существуют
    data = await state.get_data()
    subscription_message_id = data.get("subscription_message_id")
    invoice_message_id = data.get("invoice_message_id")
    if subscription_message_id:
        try:
            await callback.message.bot.delete_message(
                chat_id=callback.message.chat.id, message_id=subscription_message_id
            )
        except Exception as e:
            print(f"Ошибка удаления старого сообщения перед инвойсом: {e}")
    if invoice_message_id:
        try:
            await callback.message.bot.delete_message(
                chat_id=callback.message.chat.id, message_id=invoice_message_id
            )
        except Exception as e:
            print(f"Ошибка удаления старого инвойса: {e}")

    await state.update_data(subscription_type=subscription_type)
    # Отправляем сообщение с кнопкой "Назад" перед инвойсом
    back_button = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Назад", callback_data="back_to_subscription")]]
    )
    subscription_message = await callback.message.answer(
        f"Вы выбрали подписку на {subscription_translations.get(subscription_type, subscription_type)}. Нажмите 'Оплатить' в следующем сообщении или 'Назад' для изменения.",
        reply_markup=back_button,
    )
    await state.update_data(subscription_message_id=subscription_message.message_id)
    # Кнопка оплаты для инвойса
    pay_button = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Оплатить", pay=True)]]
    )
    invoice_message = await callback.message.bot.send_invoice(
        chat_id=callback.message.chat.id,
        title=f"Подписка на {subscription_translations.get(subscription_type, subscription_type)}",
        description=f"Доступ к боту на {subscription_translations.get(subscription_type, subscription_type)}",
        payload=f"{subscription_type}_subscription",
        provider_token="",  # Пустая строка для Telegram Stars
        currency="XTR",
        prices=prices[subscription_type],
        start_parameter="subscription",
        reply_markup=pay_button,
    )
    await state.update_data(invoice_message_id=invoice_message.message_id)


@router.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query: types.PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)


@router.message(F.successful_payment)
async def process_successful_payment(message: types.Message, state: FSMContext):
    data = await state.get_data()
    subscription_type = data.get("subscription_type")
    subscription_message_id = data.get("subscription_message_id")
    invoice_message_id = data.get("invoice_message_id")
    if subscription_message_id:
        try:
            await message.bot.delete_message(
                chat_id=message.chat.id, message_id=subscription_message_id
            )
        except Exception as e:
            print(f"Ошибка удаления сообщения перед инвойсом: {e}")
    if invoice_message_id:
        try:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=invoice_message_id)
        except Exception as e:
            print(f"Ошибка удаления инвойса: {e}")
    await add_subscription(user_id=message.from_user.id, subscription_type=subscription_type)
    await message.answer(
        f"Оплата прошла успешно! Доступ к боту на {subscription_translations.get(subscription_type, subscription_type)} активирован!",
        reply_markup=inline_kb,
    )
    await state.clear()
