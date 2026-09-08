from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, IntegerField
from wtforms.validators import DataRequired, Length, Optional, NumberRange
from models import Service


class ServiceForm(FlaskForm):
    name = StringField('Nombre del servicio', validators=[
                       DataRequired(), Length(min=2, max=100)])
    description = TextAreaField('Descripción', validators=[
                                Optional(), Length(max=500)])
    command = StringField('Comando', validators=[
                          DataRequired(), Length(min=1, max=200)])
    working_directory = StringField(
        'Directorio de trabajo', validators=[DataRequired()])
    port = IntegerField('Puerto (opcional)', validators=[
                        Optional(), NumberRange(min=1, max=65535)])
    submit = SubmitField('Guardar servicio')
