import aiosqlite
from datetime import datetime, timedelta


# Функция создания БД
async def create_table(self):
    # Создаем соединение с базой данных (если она не существует, она будет создана)
    async with aiosqlite.connect("test_users.db") as conn:
        # Создаем таблицу
        await conn.execute(
            """CREATE TABLE IF NOT EXISTS zuzubs_state (
                id INTEGER NOT NULL UNIQUE PRIMARY KEY,
                has_subscription NCHAR,
                expire_date timestamp
            )"""
        )
        # Сохраняем изменения
        await conn.commit()


# Запись в БД о покупке подписки
# К текущей дате прибавляется 30 дней (условный срок подписки)
# В итоге получается дата, с которой программа сверяется при каждом запросе пользователя
async def update_user_subscription(user_id):
    if not await check_user_existence(user_id):
        print(f"User {user_id} does not exist in the database. Creating entry.")
        return
    async with aiosqlite.connect("test_users.db") as conn:
        async with conn.cursor() as cur:
            # Проверяем текущее значение expire_date
            await cur.execute("SELECT expire_date FROM users WHERE id = ?", (user_id,))
            row = await cur.fetchone()
            print(f"Current expire_date for user {user_id}: {row}")

            # Определяем новую дату
            if row is None or row[0] is None:
                current_date = datetime.now().date()
            else:
                current_date = datetime.strptime(row[0], "%Y-%m-%d").date()

            new_expire_date = current_date + timedelta(days=30)
            print(f"New expire_date for user {user_id}: {new_expire_date}")

            # Обновляем поле expire_date
            await cur.execute(
                "UPDATE users SET expire_date = ? WHERE id = ?",
                (new_expire_date, user_id),
            )
            await conn.commit()

            # Проверяем, что обновление прошло успешно
            await cur.execute("SELECT expire_date FROM users WHERE id = ?", (user_id,))
            updated_row = await cur.fetchone()
            print(f"Updated expire_date for user {user_id}: {updated_row}")


# Проверка, существует ли пользователь в БД
async def check_user_existence(user_id) -> bool:
    async with aiosqlite.connect("test_users.db") as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = await cur.fetchone()
            if row is None:
                await cur.execute(
                    "INSERT INTO users (id, has_subscription) VALUES (?, ?)",
                    (user_id, False),
                )
                await conn.commit()
                return False
            return True


# Проверка подписки
# Если дата истечения превышает сегодняшнюю или отсутствует вообще, то бот не принимает запрос
async def check_user_rights(user_id, get_date=False) -> bool | str:
    await check_user_existence(user_id)
    async with aiosqlite.connect("test_users.db") as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT expire_date FROM users WHERE id = ?", (user_id,))
            row = await cur.fetchone()
            print(f"Checking subscription for user {user_id}: {row}")

    if get_date:
        return row[0]

    if row[0] is None:
        return False

    expire_date_object = datetime.strptime(str(row[0]), "%Y-%m-%d").date()
    if expire_date_object < datetime.now().date():
        return False
    return True
