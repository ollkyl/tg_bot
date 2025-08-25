from aiogram import Dispatcher
from .start import register_start, init_main_db as init_start_db
from .filters import register_filters
from .save_delete import register_save_delete, init_main_db as init_save_delete_db
from .subscription import register_subscription, init_main_db as init_subscription_db
from .broadcast import register_broadcast


async def init_main_db():
    """Initialize database for all handlers in main thread."""
    await init_start_db()
    await init_save_delete_db()
    await init_subscription_db()


def register_handlers(dp: Dispatcher, bot, ADMIN_ID: int):
    register_start(dp, bot)
    register_filters(dp, bot)
    register_save_delete(dp, bot)
    register_subscription(dp, bot)
    register_broadcast(dp, bot, ADMIN_ID)
