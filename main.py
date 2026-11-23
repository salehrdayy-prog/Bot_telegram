import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN
from database import init_db

from handlers.admin import router as admin_router
from handlers.filters import router as filters_router
from handlers.welcome import router as welcome_router
from handlers.help import router as help_router
from handlers.locks import router as locks_router


async def main():

    if not BOT_TOKEN:
        logging.critical("BOT_TOKEN تنظیم نشده است.")
        sys.exit(1)

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML
        )
    )

    dp = Dispatcher()

    await init_db()

    # ثبت هندلرها
    dp.include_router(help_router)
    dp.include_router(locks_router)
    dp.include_router(admin_router)
    dp.include_router(welcome_router)
    dp.include_router(filters_router)

    bot_info = await bot.get_me()

    logging.info(
        "AZRAEL started: @%s | ID: %s",
        bot_info.username,
        bot_info.id
    )

    try:
        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types(),
            drop_pending_updates=False
        )

    finally:
        await bot.session.close()


if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s"
    )

    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        logging.info("AZRAEL stopped.")
