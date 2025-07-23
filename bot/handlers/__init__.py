from aiogram import Dispatcher
from .start import register_start
from .filters import register_filters
from .save_delete import register_save_delete
from .subscription import register_subscription
from .broadcast import register_broadcast


def register_handlers(dp: Dispatcher, bot, ADMIN_ID: int):
    register_start(dp, bot)
    register_filters(dp, bot)
    register_save_delete(dp, bot)
    register_subscription(dp, bot)
    register_broadcast(dp, bot, ADMIN_ID)
