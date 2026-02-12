from flask_wtf import FlaskForm
from wtforms import IntegerField, SelectMultipleField, SubmitField
from wtforms.validators import DataRequired, NumberRange


class GrammarQuizConfigForm(FlaskForm):
    max_questions = IntegerField(
        "Max Questions",
        validators=[NumberRange(min=5, max=30)]
    )
    submit = SubmitField("Generate Quiz")


class GrammarQuizFilterForm(FlaskForm):
    lessons = SelectMultipleField(
        "Grammar Points",
        choices=[],
        validators=[DataRequired()]
    )
    submit = SubmitField("Apply Filter")
