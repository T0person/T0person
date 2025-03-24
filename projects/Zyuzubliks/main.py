import asyncio
from os import getenv
from aiogram import Bot, Dispatcher
from database import DB
import handlers
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
import logging
import sys

# Запуск процесса поллинга новых апдейтов
async def main() -> None:
    db = DB(DB_NAME)
    # Запускаем создание таблицы базы данных
    await db.create_table()

    await dp.start_polling(bot,db=db)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout) # Базовая логинация
    # Токен BotFather
    TOKEN = getenv("TOKEN")
    
    bot = Bot(TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML)) # Объект бота
    dp = Dispatcher() # Диспетчер
    DB_NAME = 'Zuzubliki.db' # Имя БД
    
    dp.include_routers(handlers.router)
    
    asyncio.run(main())