import logging
from pythonjsonlogger import jsonlogger
from logging.handlers import RotatingFileHandler


def set_json_logging(name: str) -> logging.Logger:
    """
    Создание логгера

    Args:
        name (str): Имя логгера

    Returns:
        logging.Logger: Логгер
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    file_handler = RotatingFileHandler(
        "test.log",
        maxBytes=5 * 1024 * 1024,  # Максимальный размер (5MB)
        backupCount=3,  # Количество резервных копий
        encoding="utf-8",
    )

    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s %(module)s %(funcName)s",
        json_ensure_ascii=False,
    )

    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger


logger_whisper = set_json_logging("Whisper")
logger_LLM = set_json_logging("LLM")
logger_mango = set_json_logging("Mango")
logger_google = set_json_logging("Google")
logger_main = set_json_logging("Main")
logger_diastr = set_json_logging("Pyannote")
