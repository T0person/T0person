from aiogram.types import Message, ContentType, KeyboardButton, ReplyKeyboardMarkup
from aiogram.filters import CommandStart
from aiogram import F, Router, html
import os
from database import DB
from utils import read_excel

router = Router()

def generate_main_keyboard() -> ReplyKeyboardMarkup:
    """
    Создание кнопок для телеграма

    Returns:
        ReplyKeyboardMarkup: Необходимые кнопки
    """
    kb = [[
        KeyboardButton(text="5 элементов файла"),
        KeyboardButton(text="5 элементов парсинга")
    ],
    ]
    keyboard = ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True
    )
    return keyboard

async def prepare_answer(temp:list) -> str:
    """
    Создание 'Удобочитаемого' текста для ответа

    Args:
        temp (list): Список из БД

    Returns:
        str: Основной ответ
    """
    answer = "" # Ответ
    for row in temp:
       answer +=f"{row[0]}\n{row[1]}\n{row[2]}\n" # Создание ответа
    return answer

# Стандартный хендлер для старта и приветствия
@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    start_message = f"""
    Привет, {html.bold(message.from_user.full_name)}!
    Данный бот принимает только Excel файлы!
    """
    await message.answer(start_message)

# Хендлер на принятие документа
@router.message(F.content_type == ContentType.DOCUMENT)
async def correct_handler(message : Message, db:DB) -> None:
    file_id = message.document.file_id # ID файла
    file_name = message.document.file_name # Имя файла
    
    file = await message.bot.get_file(file_id) # Подготовка файла
    
    end_path = os.path.join("documents", file_name) # Конечный путь скачивания файла
    
    await message.bot.download_file(file.file_path, end_path) # Скачивание файла
    
    keyboard = generate_main_keyboard() # Генерация кнопок
    
    # Базовая проверка разрешения файла
    if ".xlsx" in end_path:
        avg_prices = await read_excel(end_path, db) # Чтение файла
        
        answer = await prepare_answer(await db.get_file_data()) # Подготовка ответа
        
        answer +="\n\n" # Отступ для средней цены
        for title, price in avg_prices:
            answer += f"{title} - средняя цена: {round(price,2)}"
        
        await message.answer(answer, reply_markup=keyboard)
    else:
        answer = f"Не правильный документ, но я его сохранил. Мне нужны только файлы {html.bold('.xlsx Файлы Excel!!!')}"
        await message.answer(answer, reply_markup=keyboard)

# Кнопка для вывода из БД по файлам
@router.message(F.text == "5 элементов файла")
async def get_file(message : Message, db:DB) -> None:
    answer = await prepare_answer(await db.get_file_data())
    await message.answer(answer)

# Кнопка для вывода из БД по скрапингу
@router.message(F.text == "5 элементов парсинга")
async def get_products(message : Message, db:DB) -> None:
    answer = await prepare_answer(await db.get_parser_data())
    await message.answer(answer)

# Базовый ответ для ненужных действий
@router.message()
async def incorrect_handler(message : Message) -> None:
    await message.answer("На данный текст не отвечаю!")