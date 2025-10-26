import re
import gc
import sys
import torch
import time
from gspread import Spreadsheet
from datetime import datetime, timedelta
from .services_api import Mango_API, Google_API
from .models import whisper_model, LLM_model
from .templates import (
    summary_system_prompt,
    total_headers,
    type_system_prompt,
    questions,
    question_system_prompt,
    rules_questions,
    manager_script,
    rules_system_prompt,
    gramma_system_prompt,
    role_fix_system_prompt,
)
from .logger_config import logger_google, logger_mango, logger_LLM, logger_main


def check_answer(answer: str, question: str):
    pattern_yes_no = r"\(Да или Нет\)$"
    pattern_description = r"\(Описание\)$"
    pattern = (
        r"(?:напиши описание|описание|\(описание\))\s*[:]?\s*(.*?)(?=\n|$|\?|\.|;|\))"
    )
    flags = re.IGNORECASE  # игнорирует регистр букв
    if re.search(pattern_yes_no, question):
        return "Да" if "Да" in answer else "Нет"
    elif re.search(pattern_description, question):
        match = re.search(pattern, answer, flags)
        if match and match.group(1).strip():
            return match.group(1).strip()

    return answer


def main(
    mango_api: Mango_API,
    date_from: datetime,
    temp_date_to: datetime,
    table: Spreadsheet,
    table_info: dict,
) -> tuple[datetime, dict]:
    """
    Основная функция

    Args:
        mango_api (Mango_API): Экземпляр класса
        date_from (datetime): Время "от"
        temp_date_to (datetime): Время "до"
        table (Spreadsheet): Таблица
        table_info (dict): Данные о таблице

    Returns:
        tuple[datetime, dict]: Дата "от" и данные о таблице
    """
    logger_mango.info(
        f"Получение звонков {date_from.strftime("%d.%m.%Y %H:%M:%S")} - {temp_date_to.strftime("%d.%m.%Y %H:%M:%S")}"
    )
    actual_month = date_from.strftime(
        format="%m.%Y"
    )  # Получаем актуальный месяц (Для Google API)

    # Получение ключа статистики (Запуск генерации списка)
    key = mango_api.get_satistics_key(
        start_date=date_from.strftime("%d.%m.%Y %H:%M:%S"),
        end_date=temp_date_to.strftime("%d.%m.%Y %H:%M:%S"),
    )

    if "result" in key and key["result"] == 5005:
        logger_mango.error("Ошибка сервера!")
        sys.exit(1)

    # Получение списка звонков
    list_records_info = mango_api.get_records(key)

    # Если список не получен, повторяем
    if isinstance(list_records_info, dict) and len(list_records_info["data"]) == 0:
        return temp_date_to, table_info

    # Получение структурированного списка интересующих звонков
    list_records_info = mango_api.create_records_list(list_records_info)

    # Проверка на интересующие звонки
    if len(list_records_info) == 0:
        return temp_date_to, table_info

    data_rows = []
    # Обработка каждого аудио-файла
    for call_info in list_records_info:
        # Транскрибация
        audio = mango_api.get_audio_files_list(call_info[0])

        text = whisper_model.get_transcribe(audio)

        start_time = time.time()  # Начало отсчета

        # Пост обработка
        text = LLM_model.generate_answer(gramma_system_prompt, text)
        text = LLM_model.generate_answer(role_fix_system_prompt, text)

        # Генерация
        type_text = LLM_model.generate_answer(type_system_prompt, text)  # Тип разговора
        summary = LLM_model.generate_answer(summary_system_prompt, text)  # Пересказ

        # Запись данных в список
        call_info = call_info[1:] + [type_text] + [text] + [summary]

        for question in rules_questions:
            answer = LLM_model.generate_answer(
                rules_system_prompt.format(manager_script, question), text
            )
            call_info.append(check_answer(answer, question))

        for question in questions:
            answer = LLM_model.generate_answer(
                question_system_prompt.format(question), text
            )
            call_info.append(check_answer(answer, question))

        data_rows.append(call_info)

        end_time = time.time()  # Конец отсчета
        logger_LLM.info(f"Время генерации: {(end_time-start_time):.2f} секунд")

        # Очистка памяти GPU (если используется CUDA)
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        gc.collect()

    # Очистка оперативной памяти
    del list_records_info, key, summary, type_text, text, audio
    gc.collect()

    # Отправка в Google Sheets
    # Удаление старого листа и создание нового
    if "Лист1" in table_info["titles"]:
        worksheet = Google_API.create_worksheet(table, actual_month)  # Создание нового
        Google_API.delete_worksheet(table, "Лист1")  # Удаление "Лист1"
        Google_API.insert_header(worksheet, total_headers)
        logger_google.info(f"Удален стандартный лист и создан новый {actual_month}")

    # Добавление нового листа
    elif actual_month not in table_info["titles"]:
        worksheet = Google_API.create_worksheet(table, actual_month)  # Создание нового
        Google_API.insert_header(worksheet, total_headers)
        logger_google.info(f"Создан новый лист {actual_month}")

    # Добавление информации в таблицу
    table_info = Google_API.get_worksheet_info(table)  # Информация о таблице
    worksheet = table.worksheet(actual_month)
    rows = worksheet.get_all_records()
    Google_API.add_data_to_worksheet(worksheet, data_rows, len(rows) + 2)
    logger_google.info(
        f"Добавлены ячейки в лист '{actual_month}' с {len(rows) + 2} по {len(rows) + 1 + len(data_rows)} строчки"
    )

    return temp_date_to, table_info


def check_parts_days(
    date_from: datetime, date_to: datetime
) -> tuple[datetime, datetime]:
    """
    Проверка времени по прошлым пунктам

    Args:
        date_from (datetime): Дата "от"
        date_to (datetime): Дата "до"

    Returns:
        tuple[datetime, datetime]: Даты
    """
    # Сегодняшние границы рабочего времени
    today_start = date_to.replace(hour=9, minute=0, second=0, microsecond=0)
    today_end = date_to.replace(hour=21, minute=0, second=0, microsecond=0)

    if date_to < today_start:  # До начала рабочего дня
        return today_start, today_start + timedelta(hours=1)
    elif date_to > today_end:  # После окончания рабочего дня
        # Завтрашнее начало рабочего дня
        tomorrow_start = (today_start + timedelta(days=1)).replace(
            hour=9, minute=0, second=0
        )
        return tomorrow_start, tomorrow_start + timedelta(hours=1)
    else:
        return date_from, date_to


def past_days(
    mango_api: Mango_API,
    date_from: datetime,
    date_to: datetime,
    table: Spreadsheet,
    table_info: dict,
    _continue: bool = False,
):
    """
    Запуск программы с прошлых дней

    Args:
        mango_api (Mango_API): Экземпляр манго
        date_from (datetime): Дата "от"
        date_to (datetime): Дата "до"
        table (Spreadsheet): Таблица
        table_info (dict): Информация о таблице
        _continue (bool, optional): флаг с продолжением. Defaults to False.
    """

    # Работает пока дата "от" меньше даты "до"
    while date_from < date_to:

        temp_date_to = date_from + timedelta(hours=1)  # Вычисляем отрезок времени
        # Проверка на время и спать
        date_from, temp_date_to = check_parts_days(date_from, temp_date_to)

        date_from, table_info = main(
            mango_api, date_from, temp_date_to, table, table_info
        )
        gc.collect()
    if _continue:
        while True:
            date_from, date_to = mango_api.get_date(date_from, date_to)
            date_from, table_info = main(
                mango_api, date_from, date_to, table, table_info
            )
            gc.collect()


def online_work(
    mango_api: Mango_API,
    date_from: datetime,
    date_to: datetime,
    table: Spreadsheet,
    table_info: dict,
):

    while True:
        date_from, date_to = mango_api.get_date(date_from, date_to)
        date_from, table_info = main(mango_api, date_from, date_to, table, table_info)
        gc.collect()


def user_choise_logic(args):
    mango_api = Mango_API()
    client = Google_API.client_init_json()  # Инициализация клиента
    table = Google_API.get_table_by_id(client)  # Получение таблицы
    table_info = Google_API.get_worksheet_info(table)  # Информация о таблице

    # Создание таблицы с задаными днями
    if args.date_from is not None and args.date_to is not None:
        if args.date_from > args.date_to:
            print('Дата "от" не может быть больше даты "до"')
            sys.exit(1)
        logger_main.info("Запус предыдущих дней")
        past_days(mango_api, args.date_from, args.date_to, table, table_info, False)

    elif args.date_from is not None and args.date_to is None:
        logger_main.info("Запус предыдущих дней c продолжением")
        date_to = datetime.now()
        past_days(mango_api, args.date_from, date_to, table, table_info, True)

    else:
        logger_main.info("В обычном режиме")
        base_date = datetime(2000, 2, 2, 0, 0, 0)
        online_work(mango_api, base_date, base_date, table, table_info)
