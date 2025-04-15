from os import getenv
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
import logging
from bot import handler_router, callback_router
from sql import create_table


async def main():
    logging.basicConfig(level=logging.INFO)  # Базовая логинация
    bot = Bot(
        getenv("BOT_TOKEN"), default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    await create_table()

    dp.include_routers(handler_router, callback_router)

    await dp.start_polling(
        bot, allowed_updates=dp.resolve_used_update_types()
    )  # Пропуск уведомлений


if __name__ == "__main__":

    asyncio.run(main())
