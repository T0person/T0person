from datetime import datetime, timezone
from typing import Optional
import sqlalchemy as sa
import sqlalchemy.orm as so
from app import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from hashlib import md5


class User(UserMixin, db.Model):
    # ID
    id: so.Mapped[int] = so.mapped_column(primary_key=True)

    # Имя пользователя
    username: so.Mapped[str] = so.mapped_column(sa.String(64), index=True, unique=True)

    # Email пользователя
    email: so.Mapped[str] = so.mapped_column(sa.String(120), index=True, unique=True)

    # Пароль
    password_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))

    # Описание пользователя
    about_me: so.Mapped[Optional[str]] = so.mapped_column(sa.String(140))

    # Последняя активность
    last_seen: so.Mapped[Optional[datetime]] = so.mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )

    # Связь с Posts
    posts: so.WriteOnlyMapped["Post"] = so.relationship(back_populates="author")

    def __repr__(self):
        return "<User {}>".format(self.username)

    # Установка пароля
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    # Проверка пароля
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    # Генерация аватара
    def avatar(self, size):
        digest = md5(self.email.lower().encode("utf-8")).hexdigest()
        return f"https://www.gravatar.com/avatar/{digest}?d=identicon&s={size}"


@login.user_loader
def load_user(id):
    return db.session.get(User, int(id))


class Post(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    body: so.Mapped[str] = so.mapped_column(sa.String(140))
    timestamp: so.Mapped[datetime] = so.mapped_column(
        index=True, default=lambda: datetime.now(timezone.utc)
    )
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id), index=True)

    # Связь с Users
    author: so.Mapped[User] = so.relationship(back_populates="posts")

    def __repr__(self):
        return "<Post {}>".format(self.body)
