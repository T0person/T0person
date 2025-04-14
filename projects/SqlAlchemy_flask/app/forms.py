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
