from wtforms import IntegerField, SelectMultipleField
from wtforms.fields import Label
from wtforms.validators import DataRequired, NumberRange
from lingual.modules.nihongo.utils.kanji_processor import Kanji
from lingual.utils.quiz_manager import QuizForm, LessonQuizConfigForm

class GrammarQuizConfigForm(LessonQuizConfigForm):
    title = "Grammar Quiz Configuration"
    description = "Configure your grammar quiz by selecting the grammar points you want to be quizzed on and the maximum number of questions. The quiz will be generated based on the selected grammar points, so choose wisely to focus on areas you want to improve!"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.lessons.label = Label(self.lessons.id, "Grammar Points") # Assign this here too
    
    def set_lesson_choices(self, choices: list[tuple[str, str]]) -> None:
        self.lessons.choices = choices # type: ignore
        self.lessons.data = [value for value, _ in choices]  # Select all by default

class KanjiQuizConfigForm(QuizForm):
    title = "Kanji Quiz Configuration"
    description = "Configure your kanji quiz by selecting the kanji characters you want to be quizzed on and the maximum number of questions. The quiz will include questions on readings and meanings of the selected kanji, so choose characters you want to master!"

    max_questions = IntegerField(
        "Max Questions",
        validators=[NumberRange(min=5, max=50)],
        default=10
    )

    kanji_characters = SelectMultipleField(
        "Kanji Characters",
        validators=[DataRequired()]
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.kanji_characters.label = Label(self.kanji_characters.id, "Kanji Characters")
        kanji_list = [(kanji, kanji) for kanji, _ in Kanji.get_prescribed_kanji()]
        self.kanji_characters.choices = kanji_list # type: ignore
        self.kanji_characters.data = [kanji for kanji, _ in kanji_list]  # Select all by default

