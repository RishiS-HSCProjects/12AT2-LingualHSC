import json
import random
from pathlib import Path
from flask import url_for
from lingual.modules.nihongo.forms import GrammarQuizConfigForm, KanjiQuizConfigForm
from lingual.utils import quiz_manager
from .grammar_lesson_processor import get_processor

def load_quiz_data(lesson_slug: str) -> dict | None:
    base_dir = Path(get_processor().data_root) / "quizzes"
    path = base_dir / f"{lesson_slug}.json"

    if not path.exists():
        # If the quiz data file doesn't exist for the given lesson slug, return None to indicate no quiz data is available
        return None

    with path.open("r", encoding="utf-8") as f: #
        data = json.load(f)

    return get_processor().transform_data(data) # Apply any necessary transformations to the quiz data using the lesson processor's transformers (e.g. furigana transformation)

def get_grammar_lesson_choices() -> list[tuple[str, str]]:
    """
        Retrieves a list of tuples containing lesson slugs and titles for all grammar lessons.
        This is used to populate the choices for the grammar quiz configuration form.
    """
    choices: list[tuple[str, str]] = [] # Initialise empty list to hold the choices as tuples of (slug, title)
    for category in get_processor().get_lessons(): # Get categories from processor
        for lesson in category["lessons"]: # Iterate through lessons in each category
            choices.append((lesson.slug, lesson.title)) # Append a tuple of (slug, title) to the choices list
    return choices # Return lessons in tuple format!

def get_selected_grammar_lessons() -> list[str]:
    choices = get_grammar_lesson_choices() # List of tuples
    selected = [value for value, _ in choices] # Extract just the values (slugs) of the lessons
    return selected

def build_grammar_quiz(lesson_slugs: list[str], max_questions: int) -> dict:
    questions: list[dict] = []

    for lesson_slug in lesson_slugs:
        data = load_quiz_data(lesson_slug)
        if not data:
            continue

        for group_id, group in data.items():
            bank = group.get("bank", [])
            for question in bank:
                question_copy = dict(question) # Make a copy of the question dictionary to avoid mutating the original data
                question_copy["source_lesson"] = lesson_slug
                question_copy["source_group"] = group_id
                questions.append(question_copy)

    random.shuffle(questions) # Shuffle the questions to ensure a random order each time the quiz is generated
    questions = questions[:max_questions] # Limit the number of questions to the specified maximum

    return { # Return the quiz data in the expected format for the quiz manager, with a title and a bank of questions
        "title": "Grammar Quiz",
        "bank": questions
    }

class NihongoQuizTypes(quiz_manager.TypeEnum):
    """ Enumeration of quiz types for the Nihongo module, with associated descriptions and enabled status. """
    
    GRAMMAR = quiz_manager.auto()
    KANJI = quiz_manager.auto()

    @property
    def description(self) -> str:
        descriptions = {
            self.GRAMMAR: "Collate quizzes on HSC Japanese grammar points, customisable by your preference!",
            self.KANJI: "Quizzes on kanji characters, including readings and meanings! While not yet released, click below to see a preview of what Kanji Quizzes will entail!"
        }
        return descriptions.get(self, "")
    
    @property
    def is_enabled(self) -> bool:
        enabled_status = {
            self.KANJI: False # Disable kanji quiz for now until it's implemented
        }
        return enabled_status.get(self, True) # Enabled by default unless specified otherwise in the dictionary

    def get_modal(self) -> quiz_manager.QuizForm:
        """ Returns the appropriate quiz configuration form based on the quiz type. """

        if self == self.GRAMMAR:
            form = GrammarQuizConfigForm()
            form.set_action(url_for("nihongo.quiz", type=self.name))
            form.set_lesson_choices(get_grammar_lesson_choices())
            return form
        elif self == self.KANJI:
            form = KanjiQuizConfigForm()
            form.set_action(url_for("nihongo.quiz", type=self.name))
            return form

        return super().get_modal() # Raise NotImplementedError
