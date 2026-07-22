import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
import database as db
from handlers import (
    start_router,
    catalog_router,
    search_router,
    reviews_router,
    favorites_router,
    orders_router,
    admin_main_router,
    admin_products_router,
    admin_categories_router,
    admin_stats_router,
    admin_settings_router,
)

LOG_FILE = os.path.join(os.path.dirname(__file__), "bot.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # Регистрация роутеров (порядок важен — admin первым)
    dp.include_router(admin_main_router)
    dp.include_router(admin_products_router)
    dp.include_router(admin_categories_router)
    dp.include_router(admin_stats_router)
    dp.include_router(admin_settings_router)
    dp.include_router(orders_router)
    dp.include_router(favorites_router)
    dp.include_router(start_router)
    dp.include_router(catalog_router)
    dp.include_router(search_router)
    dp.include_router(reviews_router)

    await db.init_db()
    logger.info("Database initialized")

    logger.info("Starting bot...")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await db.close_pool()
        await bot.session.close()
        logger.info("Bot stopped.")


if __name__ == "__main__":
    asyncio.run(main())
