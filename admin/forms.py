from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, BooleanField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError
from models import User


class UserForm(FlaskForm):
    username = StringField('Usuario', validators=[
                           DataRequired(), Length(min=2, max=20)])
    role = SelectField('Rol', choices=[
                       ('user', 'Usuario'), ('admin', 'Administrador')], validators=[DataRequired()])
    is_active = BooleanField('Cuenta activa')
    submit = SubmitField('Guardar usuario')


class UserCreateForm(UserForm):
    password = PasswordField('Contraseña', validators=[
                             DataRequired(), Length(min=6)])
    password2 = PasswordField(
        'Repetir contraseña', validators=[DataRequired(), EqualTo('password')]
    )

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Elige un usuario diferente.')


class UserEditForm(UserForm):
    password = PasswordField(
        'Nueva contraseña (deja vacío para conservarla)', validators=[Length(min=6)])
    password2 = PasswordField(
        'Repetir nueva contraseña', validators=[EqualTo('password')]
    )

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=username.data).first()
            if user is not None:
                raise ValidationError('Elige un usuario diferente.')


class SettingsForm(FlaskForm):
    npm_bin_path = StringField(
        'Ruta del ejecutable de npm', validators=[Length(max=500)])
    node_path = StringField(
        'Ruta del ejecutable de Node.js', validators=[Length(max=500)])
    python_env_path = StringField(
        'Ruta del entorno virtual de Python', validators=[Length(max=500)])
    submit = SubmitField('Guardar rutas globales')
