from datetime import datetime, timezone
from typing import Optional
import sqlalchemy as sa
import sqlalchemy.orm as so
from app import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from hashlib import md5

# Самореферентная таблица подписчиков
followers = sa.Table(
    "followers",  # Имя таблицы
    db.metadata,  # Метаданные (Информация обо всех таблицах в БД)
    sa.Column(
        "follower_id", sa.Integer, sa.ForeignKey("user.id"), primary_key=True
    ),  # Составные первичные ключи
    sa.Column("followed_id", sa.Integer, sa.ForeignKey("user.id"), primary_key=True),
)


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

    ## ---------Подписки и прочее, что к ним относится

    # Связь, где видно список пользователей, на которых пользователь подписывается
    following: so.WriteOnlyMapped["User"] = so.relationship(
        secondary=followers,  # Настройка ассоциаций
        primaryjoin=(followers.c.follower_id == id),  # Соответствия с атрибутами
        secondaryjoin=(followers.c.followed_id == id),
        back_populates="followers",  # Связь с моделью
    )
    # Связь, где видно список пользователей, которые подписаны на пользователя
    followers: so.WriteOnlyMapped["User"] = so.relationship(
        secondary=followers,
        primaryjoin=(followers.c.followed_id == id),
        secondaryjoin=(followers.c.follower_id == id),
        back_populates="following",  # Связь с моделью
    )

    # Подписаться
    def follow(self, user):
        if not self.is_following(user):
            self.following.add(user)

    # Отписаться
    def unfollow(self, user):
        if self.is_following(user):
            self.following.remove(user)

    # Проверка на существующую подписку
    def is_following(self, user):
        query = self.following.select().where(User.id == user.id)
        return db.session.scalar(query) is not None

    # Количество подписчиков
    def followers_count(self):
        query = sa.select(sa.func.count()).select_from(
            self.followers.select().subquery()  # Подзапрос
        )
        return db.session.scalar(query)

    # Количество подписок
    def following_count(self):
        query = sa.select(sa.func.count()).select_from(
            self.following.select().subquery()  # Подзапрос
        )
        return db.session.scalar(query)

    def following_posts(self):
        Author = so.aliased(User)  # Ссылка на User модель для автора
        Follower = so.aliased(User)  # Ссылка на User модель для подписчика
        return (
            sa.select(Post)  # Выборка постов
            .join(Post.author.of_type(Author))  # Объединение, дальнейшая ссылка Author
            .join(
                Author.followers.of_type(Follower), isouter=True
            )  # Объединение левой стороны без соответсвий справа (внешнее объединение)
            # Получаем посты автора и подписок
            .where(
                sa.or_(
                    Follower.id == self.id,
                    Author.id == self.id,
                )
            )
            .group_by(Post)  # Группировка по всем полям постов
            .order_by(Post.timestamp.desc())  # Сортировка
        )


# Функция загрузки Flask-Login user
@login.user_loader
def load_user(id):  # Принимается строка, необходимо перевести в число
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
