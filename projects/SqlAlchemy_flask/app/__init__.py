from flask import Flask
from .config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
import logging
from logging.handlers import RotatingFileHandler
import os


app = Flask(__name__)  # Инициализация приложения
app.config.from_object(Config)  # Из config.py берем необходимые настройки конфигурации

login = LoginManager(app)  # Инициализация логинации
login.login_view = (
    "login"  # Не аутентифицированный пользователь перенаправляется на этот URL
)

db = SQLAlchemy(app)  # Инициализация БД
migrate = Migrate(app, db)  # Инициализация миграции БД

# Запись логов в
if not app.debug:

    # Создание файла если его нет
    if not os.path.exists("logs"):
        os.mkdir("logs")

    # Запись в файл
    file_handler = RotatingFileHandler(
        "logs/product.log",  # Путь
        maxBytes=10240,  # Максимальный размер файла
        backupCount=10,  # Количество файлоа
    )

    # Форматтер для логов
    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
        )
    )
    # Установка уровня логов
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)

    app.logger.setLevel(logging.INFO)
    app.logger.info("Приложение запущено!")


from app import routes, models, errors
