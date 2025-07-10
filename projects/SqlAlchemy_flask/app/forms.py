from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from .models import User
import sqlalchemy as sa
from app import db
from wtforms import TextAreaField
from wtforms.validators import Length


class LoginForm(FlaskForm):
    """
    Форма логинации

    Args:
        FlaskForm (_type_): Наследование формы
    """

    username = StringField(
        "Username", validators=[DataRequired()]
    )  # Строковое поле имени
    password = PasswordField("Password", validators=[DataRequired()])  # Парольное поле
    remember_me = BooleanField("Remember Me")  # Checkbox
    submit = SubmitField("Sign In")  # Кнопка


class RegistrationForm(FlaskForm):
    """
    Форма регистрации

    Args:
        FlaskForm (_type_): Наследование формы

    Raises:
        ValidationError: Ошибка email-а и пароля
    """

    # Строковое поле имени
    username = StringField("Username", validators=[DataRequired()])

    # Строковое поле email-а
    email = StringField("Email", validators=[DataRequired(), Email()])

    # Парольное поле
    password = PasswordField("Password", validators=[DataRequired()])

    # Парольное поле проверки
    password2 = PasswordField(
        "Repeat Password", validators=[DataRequired(), EqualTo("password")]
    )
    # Кнопка
    submit = SubmitField("Register")

    # Проверка имени
    def validate_username(self, username):
        user = db.session.scalar(sa.select(User).where(User.username == username.data))
        if user is not None:
            raise ValidationError("Используйте другое имя.")

    # Проверка email-а
    def validate_email(self, email):
        user = db.session.scalar(sa.select(User).where(User.email == email.data))
        if user is not None:
            raise ValidationError("Используйте другой email.")


class EditProfileForm(FlaskForm):
    """
    Форма редактора профиля

    Args:
        FlaskForm (_type_): Наследование формы
    """

    username = StringField("Username", validators=[DataRequired()])
    about_me = TextAreaField("About me", validators=[Length(min=0, max=140)])
    submit = SubmitField("Submit")

    def __init__(self, original_username, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_username = (
            original_username  # Получение исходного имени пользователя
        )

    # Функция проверки имени
    def validate_username(self, username):
        # Если введеное имя другое
        if username.data != self.original_username:
            # Проверка в базе данных
            user = db.session.scalar(
                sa.select(User).where(User.username == self.username.data)
            )
            if user is not None:
                raise ValidationError("Используйте другое имя!")


# Форма для подписок и отписок
class EmptyForm(FlaskForm):
    submit = SubmitField("Submit")


# Форма создания поста
class PostForm(FlaskForm):
    post = TextAreaField(
        "Напиши что-нибудь", validators=[DataRequired(), Length(min=1, max=140)]
    )
    submit = SubmitField("Submit")
