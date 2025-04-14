from flask import Flask
from .config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager


app = Flask(__name__)  # Инициализация приложения
app.config.from_object(Config)  # Из config.py берем необходимые настройки конфигурации

login = LoginManager(app)  # Инициализация логинации
login.login_view = (
    "login"  # Не аутентифицированный пользователь перенаправляется на этот URL
)

db = SQLAlchemy(app)  # Инициализация БД
migrate = Migrate(app, db)  # Инициализация миграции БД
from app import routes, models
