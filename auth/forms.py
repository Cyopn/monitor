from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError
from models import User


class LoginForm(FlaskForm):
    username = StringField('Usuario', validators=[
                           DataRequired(), Length(min=2, max=20)])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    remember = BooleanField('Recordarme')
    submit = SubmitField('Iniciar sesión')


class RegistrationForm(FlaskForm):
    username = StringField('Usuario', validators=[
                           DataRequired(), Length(min=2, max=20)])
    password = PasswordField('Contraseña', validators=[
                             DataRequired(), Length(min=6)])
    password2 = PasswordField(
        'Repetir contraseña', validators=[DataRequired(), EqualTo('password')]
    )
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Elige un usuario diferente.')
