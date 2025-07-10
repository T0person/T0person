from dotenv import load_dotenv

load_dotenv()
from utils import user_choise_logic
from datetime import datetime
import argparse


def valid_date(date_str: str) -> datetime:
    try:
        return datetime.strptime(date_str, "%d.%m.%Y %H:%M:%S")
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Неправильный формат даты. Ожидается: ДД.ММ.ГГГГ ЧЧ:ММ:СС (например: 19.0 6.2023 15:30:00)"
        )


if __name__ == "__main__":
    # Определение парсера
    parser = argparse.ArgumentParser(
        description="Скрипт транскрибации аудио-звонков в Google Sheets"
    )

    # Определение аргументов для парсинга
    parser.add_argument(
        "-df",
        "--date_from",
        type=valid_date,
        help="Дата и время в формате 'ДД.ММ.ГГГГ ЧЧ:ММ:СС' (например: '19.06.2023 15:30:00')",
    )

    parser.add_argument(
        "-dt",
        "--date_to",
        type=valid_date,
        help="Дата и время в формате 'ДД.ММ.ГГГГ ЧЧ:ММ:СС' (например: '19.06.2023 15:30:00')\
            или\
                'now' для продолжения в обычном режиме",
    )

    # Получение аргументов
    args = parser.parse_args()

    # Анализ выбора пользователя
    user_choise_logic(args)
