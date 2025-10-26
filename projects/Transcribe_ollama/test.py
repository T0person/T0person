import hashlib
from os import getenv
from dotenv import load_dotenv
from typing import Callable, Any
import json
import requests
from datetime import datetime

load_dotenv()


class MangoAPI:
    # Данные авторизации
    api_key = getenv("MANGO_API")
    api_salt = getenv("MANGO_SALT")

    # Формат кодирования данных
    header = {"Content-type": "application/x-www-form-urlencoded"}

    # Округление времени
    round_date = lambda dt: dt.replace(
        minute=(dt.minute // 10) * 10, second=0, microsecond=0
    )

    # Хеширование данных
    hash = lambda api, data, salt: hashlib.sha256(
        (api + data + salt).encode("utf-8")
    ).hexdigest()
    # Проверка Post-ответа
    check_status_code: Callable[[int], bool] = lambda sc: (True if sc == 200 else False)

    @classmethod
    def __generate_body(cls, data) -> dict[str, Any]:
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
            "vpbx_api_key": cls.api_key,
            "sign": cls.hash(cls.api_key, data, cls.api_salt),
            "json": data,
        }
        return body

    @classmethod
    def __get_satistics_key(cls, start_datetime: str, end_datetime: str) -> dict:
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
            "start_date": start_datetime,  # Начало отрезка
            "end_date": end_datetime,  # Конец отрезка
            "limit": "500",  # Лимит получения данных (не более)
            "offset": "0",  # Сдвиг по времени
        }

        body = cls.__generate_body(data)  # Генерация тела запроса

        # Отправка Post-запроса
        response = requests.post(url, headers=cls.header, data=body)

        # Если получение неправильно статуса запроса
        if not cls.check_status_code(response.status_code):
            error_message = {"code": response.status_code, "content": response.content}
            # logger_mango.error("Ошибка получения статистики", extra=error_message)
            # sys.exit(1)

        # logger_mango.info("Ключ статистики получен")
        return response.json()

    @classmethod
    def __get_records(cls, key: dict) -> dict:
        """
        Получение списка звонков

        Args:
            key (dict): Ключ

        Returns:
            dict: Список звонков
        """

        # Базовый URL ил расширенный
        url = str(getenv("EXPAND_RECORDS_URL"))

        body = cls.__generate_body(key)  # Генерация тела запроса

        # Отправка Post-запроса
        response = requests.post(url, headers=cls.header, data=body)

        #  Проверка на неправильный ответ
        if not cls.check_status_code(response.status_code):
            error_message = {
                "code": response.status_code,
                "content": response.content,
            }
            # logger_mango.error(
            #     "Ошибка получения информации о звонках", extra=error_message
            # )
            # sys.exit(1)

        # Возврат информации
        # logger_mango.info("Получение расширенной информации о звонках")
        return response.json()

    @staticmethod
    def __create_records_list(records_list: dict) -> list:
        """
        Выборка звонков клиент-сотрудник и составление списка звонков

        Args:
            records_list (dict): Список звонков в формате текста

        Returns:
            list: Выборка звонков
        """
        calls = []

        # Структуризация звонков
        for call in records_list["data"][0]["list"][::-1]:
            if call["context_status"] == 1:
                match call["context_type"]:
                    # Входящий
                    case 1:
                        client_number = call["caller_name"]
                        _timestamp = float(call["context_calls"][0]["call_start_time"])
                        date = datetime.fromtimestamp(_timestamp).strftime(
                            "%d.%m.%Y %H:%M:%S"
                        )

                        try:
                            manager_name = call["context_calls"][0]["members"][0][
                                "call_abonent_info"
                            ]
                        except:
                            manager_name = call["called_number"]
                            error = {"datetime": date}
                            # logger_mango.warning("Нет имени сотрудника!", extra=error)
                        try:
                            recording_id = call["context_calls"][0]["recording_id"][0]

                            calls.append(
                                [recording_id, date, client_number, manager_name]
                            )
                        except:
                            continue
                    # Исходящий
                    case 2:
                        if len(call["context_calls"][0]["recording_id"]) != 0:
                            manager_name = call["caller_name"]
                            _timestamp = call["context_calls"][0]["call_start_time"]
                            date = datetime.fromtimestamp(_timestamp).strftime(
                                "%d.%m.%Y %H:%M:%S"
                            )
                            client_number = call["called_number"]
                            recording_id = call["context_calls"][0]["recording_id"][0]
                            calls.append(
                                [recording_id, date, manager_name, client_number]
                            )
        return calls

    @classmethod
    def get_list_records(cls, start_datetime: str, end_datetime: str):
        key = cls.__get_satistics_key(start_datetime, end_datetime)
        list_records_info = cls.__get_records(key)

        # print(list_records_info)
        return (
            False
            if len(list_records_info["data"]) == 0
            else MangoAPI.__create_records_list(list_records_info)
        )


if __name__ == "__main__":

    # ДОБАВИТЬ ПОЛУЧЕНИЕ ДАННЫХ ИЗ БД ПРИ НАЧАЛЕ РАБОТЫ
    
    # Получение записей
    print(MangoAPI.get_list_records("18.07.2025 09:00:00", "18.07.2025 09:05:00"))
