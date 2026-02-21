import re
from lingual.utils.languages import Languages
from lingual.utils.lesson_processor import BaseLessonProcessor

FURIGANA_RE = re.compile(r'([一-龯々]+)\[([^\]]+)\]')

class TutorialLessonProcessor(BaseLessonProcessor):
    """
    Lesson processor for Tutorial module.
    Registers additional transformers specific to Tutorial lessons.
    """

    def __init__(self):
        from pathlib import Path

        BASE_DIR = Path(__file__).resolve().parents[1]

        DIR = BASE_DIR / "data" / "lessons"

        super().__init__(
            language = Languages.TUTORIAL.obj(),
            data_root = DIR
        )
    
_PROCESSOR: TutorialLessonProcessor | None = None

def get_processor() -> TutorialLessonProcessor:
    global _PROCESSOR
    if _PROCESSOR is None:
        _PROCESSOR = TutorialLessonProcessor()
    return _PROCESSOR
