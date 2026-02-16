from wtforms import IntegerField, SelectMultipleField, SubmitField
from wtforms.validators import DataRequired, NumberRange
from lingual.utils.quiz_manager import QuizForm

class GrammarQuizConfigForm(QuizForm):
    title = "Grammar Quiz Configuration"
    description = "Configure your grammar quiz by selecting the grammar points you want to be quizzed on and the maximum number of questions. The quiz will be generated based on the selected grammar points, so choose wisely to focus on areas you want to improve!"

    max_questions = IntegerField(
        "Max Questions",
        validators=[NumberRange(min=5, max=30)],
        default=10
    )

    lessons = SelectMultipleField(
        "Grammar Points",
        choices=[],
        validators=[DataRequired()]
    )
    submit = SubmitField("Generate Quiz")

    def set_lesson_choices(self, choices: list[tuple[str, str]]) -> None:
        self.lessons.choices = choices # type: ignore
