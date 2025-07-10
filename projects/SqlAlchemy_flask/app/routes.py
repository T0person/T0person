from app import app, db
from flask import render_template, flash, redirect, url_for, request
from .forms import LoginForm, PostForm, RegistrationForm, EditProfileForm, EmptyForm
from urllib.parse import urlsplit
from flask_login import current_user, login_required, login_user, logout_user
import sqlalchemy as sa
from .models import User, Post
from datetime import datetime, timezone


@app.route("/", methods=["GET", "POST"])
@app.route("/index", methods=["GET", "POST"])
@login_required
def index():
    form = PostForm()  # Создание формы
    if form.validate_on_submit():
        post = Post(body=form.post.data, author=current_user)  # Модель поста
        db.session.add(post)
        db.session.commit()
        flash("Пост загружен!")
        return redirect(url_for("index"))
    posts = db.session.scalars(current_user.following_posts()).all()
    return render_template("index.html", title="Home Page", form=form, posts=posts)


# Логинация
@app.route("/login", methods=["GET", "POST"])
def login():
    # Если юзер зарегистрирован (уже есть в бд)
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    # Получение данных с формы
    form = LoginForm()

    # Проверка заполненности формы
    if form.validate_on_submit():

        # Выборка юзера
        user = db.session.scalar(
            sa.select(User).where(User.username == form.username.data)
        )

        # Проверка пароля, если есть пользователь
        if user is None or not user.check_password(form.password.data):
            flash("Неправильное имя пользователя или пароль!")
            return redirect(url_for("login"))

        # Логинация пользователя
        login_user(user, remember=form.remember_me.data)

        # Получаем страницу в поле next в строке запроса
        # Для перенаправления пользователя после логинации
        next_page = request.args.get("next")

        # Если нет поля next, возвращаем пользователя на главную страницу
        if not next_page or urlsplit(next_page).netloc != "":
            next_page = url_for("index")

        return redirect(next_page)

    # Если форма неправильно заполнена
    return render_template("login.html", title="Sign In", form=form)


# Выход из системы
@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("index"))


# Страница регистрации
@app.route("/register", methods=["GET", "POST"])
def register():
    # Если пользователь аутентифицирован
    if current_user.is_authenticated:
        # Перенаправление
        return redirect(url_for("index"))

    form = RegistrationForm()

    # Если форма правильно заполнена
    if form.validate_on_submit():
        user = User(
            username=form.username.data, email=form.email.data
        )  # Создание пользователя
        user.set_password(form.password.data)  # Создание пароля
        db.session.add(user)  # Добавление в БД
        db.session.commit()  # Отправка в БД
        flash("Congratulations, you are now a registered user!")  # Уведомление
        return redirect(url_for("login"))  # Перенаправление

    # Если неправильно заполнена форма, возврат страницы
    return render_template("register.html", title="Register", form=form)


# Страница профиля пользователя
@app.route("/user/<username>")
@login_required
def user(username):
    # Поиск пользователя или получение 404 ошибки
    user = db.first_or_404(sa.select(User).where(User.username == username))
    # Посты
    posts = [
        {"author": user, "body": "Test post #1"},
        {"author": user, "body": "Test post #2"},
    ]
    form = EmptyForm()  # Создание формы подсписки
    # Рендер страницы
    return render_template("user.html", user=user, posts=posts, form=form)


# Обновление последнего посещения
@app.before_request
def before_request():
    # Если пользователь аутентифицирован
    if current_user.is_authenticated:
        current_user.last_seen = datetime.now(timezone.utc)  # Получение времени
        db.session.commit()  # Отправка в БД


@app.route("/edit_profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)

    # Если правильно заполнена форма
    if form.validate_on_submit():
        # Изменение данных
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash("Your changes have been saved.")
        return redirect(url_for("edit_profile"))
    # Если GET заполенение формы
    elif request.method == "GET":
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template("edit_profile.html", title="Edit Profile", form=form)


# Маршрут подписки
@app.route("/follow/<username>", methods=["POST"])
@login_required
def follow(username):
    form = EmptyForm()  # Создание формы
    if form.validate_on_submit():  # Проверка токена CSRF
        user = db.session.scalar(
            sa.select(User).where(User.username == username)
        )  # Поиск пользователя
        if user is None:
            flash(f"Пользователь {username} не найден.")
            return redirect(url_for("index"))
        if user == current_user:  # Если сам на себя
            flash("Ты не можешь подписаться на себя!")
            return redirect(url_for("user", username=username))
        current_user.follow(user)
        db.session.commit()
        flash(f"Ты подписан на {username}!")
        return redirect(url_for("user", username=username))
    # Если токен не действителен
    else:
        return redirect(url_for("index"))


# Маршрут отписки
@app.route("/unfollow/<username>", methods=["POST"])
@login_required
def unfollow(username):
    form = EmptyForm()  # Создание формы
    if form.validate_on_submit():
        user = db.session.scalar(sa.select(User).where(User.username == username))
        if user is None:
            flash(f"Пользователь {username} не найден.")
            return redirect(url_for("index"))
        if user == current_user:
            flash("ты не можешь отписаться от себя")
            return redirect(url_for("user", username=username))
        current_user.unfollow(user)
        db.session.commit()
        flash(f"Ты не подписан на {username}.")
        return redirect(url_for("user", username=username))
    else:
        return redirect(url_for("index"))


# Просмотр всех сообщений
@app.route("/explore")
@login_required
def explore():
    query = sa.select(Post).order_by(Post.timestamp.desc())
    posts = db.session.scalars(query).all()
    return render_template("index.html", title="Explore", posts=posts)
