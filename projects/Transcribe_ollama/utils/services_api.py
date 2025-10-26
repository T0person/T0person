import gc
import io
import sys
import json
import hashlib
import requests
from os import getenv
from time import sleep
from typing import Callable
from datetime import datetime, timedelta
from .logger_config import logger_mango
from gspread import Client, Spreadsheet, Worksheet, service_account
import torch


def sleep_until(remaining):
    """Спит до указанного времени datetime"""
    gc.collect()
    # Очистка памяти GPU (если используется CUDA)
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    _hours = remaining // 3600
    _minutes = (remaining % 3600) // 60
    _seconds = remaining % 60
    logger_mango.info(f"Спим {_hours}:{_minutes}:{_seconds}")

    while True:
        if remaining <= 0:
            break
        sleep_time = min(1, remaining)
        sleep(sleep_time)
        remaining -= sleep_time  # Уменьшаем оставшееся время


def check_time(now: datetime):
    """
    Проверка времени

    Args:
        now (datetime): Время сейчас

    Returns:
        _type_: Время спать и актуальный отрезок времени
    """
    # Сегодняшние границы рабочего времени
    today_start = now.replace(hour=9, minute=10, second=0, microsecond=0)
    today_end = now.replace(hour=21, minute=0, second=0, microsecond=0)

    get_start_time = lambda _date: _date - timedelta(minutes=10)

    if now < today_start:  # До начала рабочего дня
        sleep_seconds = (today_start - datetime.now()).total_seconds()
        return sleep_seconds, get_start_time(today_start), today_start
    elif now > today_end:  # После окончания рабочего дня
        # Завтрашнее начало рабочего дня
        tomorrow_start = today_start + timedelta(days=1)
        sleep_seconds = (tomorrow_start - datetime.now()).total_seconds()
        return sleep_seconds, get_start_time(tomorrow_start), tomorrow_start
    else:  # Сейчас рабочее время
        actual_now = datetime.now() + timedelta(minutes=2)
        sleep_seconds = (now - actual_now).total_seconds() if now > actual_now else 0
        return sleep_seconds, get_start_time(now), now


class Mango_API:
    def __init__(self) -> None:

        # Данные авторизации
        self.vpbx_api_key = getenv("MANGO_API")
        self.api_salt = getenv("MANGO_SALT")

        # Формат кодирования данных
        self.header = {"Content-type": "application/x-www-form-urlencoded"}

        # Округление времени
        self.round_date = lambda dt: dt.replace(
            minute=(dt.minute // 10) * 10, second=0, microsecond=0
        )
        # Хеширование данных
        self.hash = lambda api, data, salt: hashlib.sha256(
            (api + data + salt).encode("utf-8")
        ).hexdigest()
        # Проверка Post-ответа
        self.check_status_code: Callable[[int], bool] = lambda sc: (
            True if sc == 200 else False
        )

    def get_date(self, date_from: datetime, date_to: datetime):
        """
        Получение актуальной даты

        Returns:
            tuple[int, int]: Дата "до" и дата "от"
        """

        # Если дата неизвестна (Первый запуск), создаем промежуток
        if date_from == datetime(2000, 2, 2, 0, 0, 0):
            # Получаем актульную дату ("до")
            date_to = datetime.now().replace(microsecond=0)
            date_to = self.round_date(date_to)
            date_from = date_to - timedelta(minutes=10)  # Дата "от"

        # Если дата известна (Следующий запуск), обновляем промежуток
        else:
            date_to += timedelta(minutes=10)

        # Проверка на время и спать
        remaining, date_from, date_to = check_time(date_to)
        if remaining > 0:
            sleep_until(remaining)

        return date_from, date_to

    def generate_body(self, data: dict):
        """
        Генерация тела запроса

        Args:
            data (dict[str, str]): Данные для запроса

        Returns:
            _type_: Тело запроса
        """
        data = json.dumps(data, separators=(",", ":"))  # Перевод в строку для отправки
        # Тело запроса
        body = {
            "vpbx_api_key": self.vpbx_api_key,
            "sign": self.hash(self.vpbx_api_key, data, self.api_salt),
            "json": data,
        }
        return body

    def get_satistics_key(self, start_date: str, end_date: str) -> dict:
        """
        Запуск генерации списка вызовов

        Args:
            start_date (str): Дата "от"
            end_date (str): Дата "до"

        Returns:
            dict: Овет json
        """
        # Если расширенная статистика
        url = str(getenv("EXPAND_STATISTIC_URL"))  # URL расширенной статистики
        data = {
            "start_date": start_date,  # Начало отрезка
            "end_date": end_date,  # Конец отрезка
            "limit": "500",  # Лимит получения данных (не более)
            "offset": "0",  # Сдвиг по времени
        }

        body = self.generate_body(data)  # Генерация тела запроса

        # Отправка Post-запроса
        response = requests.post(url, headers=self.header, data=body)

        # Если получение неправильно статуса запроса
        if not self.check_status_code(response.status_code):
            error_message = {"code": response.status_code, "content": response.content}
            logger_mango.error("Ошибка получения статистики", extra=error_message)
            sys.exit(1)

        logger_mango.info("Ключ статистики получен")
        return response.json()

    def get_records(self, key: dict) -> dict:
        """
        Получение списка звонков

        Args:
            key (dict): Ключ

        Returns:
            dict: Список звонков
        """

        while True:

            # Базовый URL ил расширенный
            url = str(getenv("EXPAND_RECORDS_URL"))

            body = self.generate_body(key)  # Генерация тела запроса

            # Отправка Post-запроса
            response = requests.post(url, headers=self.header, data=body)

            #  Проверка на неправильный ответ
            if not self.check_status_code(response.status_code):
                error_message = {
                    "code": response.status_code,
                    "content": response.content,
                }
                logger_mango.error(
                    "Ошибка получения информации о звонках", extra=error_message
                )
                sys.exit(1)

            # Возврат информации
            logger_mango.info("Получение расширенной информации о звонках")
            return response.json()

    def create_records_list(self, records_list: dict) -> list:
        """
        Фильтрация и структуризация звонков клиент-сотрудник.

        Args:
            records_list (dict): Сырые данные о звонках из API

        Returns:
            list: Список отформатированных записей звонков в виде:
                [recording_id, date, caller, receiver]
        """
        calls = []

        for call in reversed(records_list["data"][0]["list"]):
            if call["context_status"] != 1:
                continue

            context_call = call["context_calls"][0]
            call_type = call["context_type"]

            # Пропускаем звонки без записи
            if call_type == 2 and not context_call["recording_id"]:
                continue

            # Обработка временной метки
            timestamp = float(context_call["call_start_time"])
            date = datetime.fromtimestamp(timestamp).strftime("%d.%m.%Y %H:%M:%S")

            # Получение recording_id (для всех валидных случаев)
            recording_id = context_call["recording_id"][0]

            # Обработка разных типов звонков
            if call_type == 1:  # Входящий
                client_number = call["caller_name"]

                try:
                    manager_name = context_call["members"][0]["call_abonent_info"]
                except (KeyError, IndexError):
                    manager_name = call["called_number"]
                    logger_mango.warning(
                        "Нет имени сотрудника!", extra={"datetime": date}
                    )

                calls.append([recording_id, date, client_number, manager_name])

            elif call_type == 2:  # Исходящий
                manager_name = call["caller_name"]
                client_number = call["called_number"]
                calls.append([recording_id, date, manager_name, client_number])

        return calls

    def get_audio_files_list(self, recording_id: str) -> io.BytesIO:
        """
        Получение аудио-записей

        Args:
            recording_id (str): ID звонков

        Returns:
            io.BytesIO: Аудозапись
        """
        url = str(getenv("AUDIO_URL"))  # URL для получения аудио
        # Скачивание доступных аудио-файлов

        # Заполнение данных
        data = {"recording_id": recording_id, "action": "download"}

        body = self.generate_body(data)  # Генерация тела запроса

        # Отправка Post-запроса
        response = requests.post(url, headers=self.header, data=body)

        # Если получение неправильно статуса запроса
        if not self.check_status_code(response.status_code):
            error_message = {
                "code": response.status_code,
                "content": response.content,
            }
            while response.status_code == 429:
                logger_mango.error(
                    "Слишком много запросов, спим 2 секунды", extra=error_message
                )
                sleep(2)
                response = requests.post(url, headers=self.header, data=body)
            else:
                logger_mango.error("Ошибка получения аудио файла", extra=error_message)

        # Запись аудио в байтах
        return io.BytesIO(response.content)


class Google_API:
    @staticmethod
    def client_init_json() -> Client:
        """Создание клиента для работы с Google Sheets."""
        return service_account(str(getenv("GOOGLE_KEY")))

    @staticmethod
    def get_table_by_id(client: Client) -> Spreadsheet:
        """Получение таблицы из Google Sheets по ID таблицы."""
        return client.open_by_key(str(getenv("TABLE_ID")))

    @staticmethod
    def create_worksheet(table: Spreadsheet, title: str) -> Worksheet:
        """Создание листа в таблице."""
        return table.add_worksheet(title, 10_000, 100)

    @staticmethod
    def delete_worksheet(table: Spreadsheet, title: str):
        """Удаление по названию листа из таблицы."""
        table.del_worksheet(table.worksheet(title))

    @staticmethod
    def get_worksheet_info(table: Spreadsheet) -> dict:
        """Возвращает количество листов в таблице и их названия."""
        worksheets = table.worksheets()
        worksheet_info = {
            "count": len(worksheets),
            "titles": [worksheet.title for worksheet in worksheets],
        }
        return worksheet_info

    @staticmethod
    def add_data_to_worksheet(worksheet, rows: list[list[str]], start_row: int):
        """Много строчная вставка данных в лист"""
        worksheet.insert_rows(rows, row=start_row)

    @staticmethod
    def insert_header(worksheet, data: list, index: int = 1):
        """Вставка данных в лист."""
        worksheet.insert_row(data, index=index)
