from sqlite3 import Row
from typing import Iterable
import aiosqlite

class DB:
    
    def __init__(self, DB_NAME) -> None:
        self.DB_NAME = DB_NAME
    
    # Функция создания БД
    async def create_table(self) -> None:
        """
        Создание базы данных и таблиц
        """
        # Создаем соединение с базой данных (если она не существует, она будет создана)
        async with aiosqlite.connect(self.DB_NAME) as db:
            # Создаем таблицу
            await db.execute(
                '''CREATE TABLE IF NOT EXISTS zuzubs_state (
                    title NCHAR PRIMARY KEY,
                    url NCHAR, 
                    xpath NCHAR
                )''')
            await db.execute(
                '''CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY,
                    store NCHAR,
                    title NCHAR,
                    price NCHAR
                )''')
            # Сохраняем изменения
            await db.commit()
    
    async def update_file_data(self, rows:tuple) -> None:
        """
        Обновление БД по содержанию файлов

        Args:
            rows (type): Значение необходимые внести за одно подключение
        """
        # Создаем соединение с базой данных (если она не существует, она будет создана)
        async with aiosqlite.connect(self.DB_NAME) as db:
            # Вставляем новую запись или заменяем ее, если с данным user_id уже существует
            await db.executemany(
                'INSERT OR REPLACE INTO zuzubs_state (title, url, xpath) VALUES (?, ?, ?)',
                rows)
            # Сохраняем изменения
            await db.commit()
            
    async def get_file_data(self) -> Iterable[Row]:
        """
        Получение данных из таблицы по файлам

        Returns:
            Iterable[Row]: Строчки из таблицы
        """
        # Подключаемся к базе данных
        async with aiosqlite.connect(self.DB_NAME) as db:
            # Получение имени пользователя и ответы
            async with db.execute("SELECT title, url, xpath FROM zuzubs_state LIMIT 5") as cursor:
                return await cursor.fetchall()
    
    async def update_parser_data(self, rows:tuple) -> None:
        """
        Обновление БД в таблице по парсингу

        Args:
            rows (tuple): Значение необходимые внести за одно подключение
        """
        # Создаем соединение с базой данных (если она не существует, она будет создана)
        async with aiosqlite.connect(self.DB_NAME) as db:
            # Вставляем новую запись или заменяем ее, если с данным user_id уже существует
            await db.executemany(
                'INSERT OR REPLACE INTO products (id, store, title, price) VALUES (?, ?, ?, ?)',
                rows)
            # Сохраняем изменения
            await db.commit()
    
    async def get_parser_data(self) -> Iterable[Row]:
        """
        Получение данных из таблицы по парсингу

        Returns:
            Iterable[Row]: Строчки из таблицы
        """
        # Подключаемся к базе данных
        async with aiosqlite.connect(self.DB_NAME) as db:
            # Получение имени пользователя и ответы
            async with db.execute("SELECT store, title, price FROM products LIMIT 5") as cursor:
                return await cursor.fetchall()