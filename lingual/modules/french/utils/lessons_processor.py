import re
from lingual.utils.languages import Languages
from lingual.utils.lesson_processor import BaseLessonProcessor

FURIGANA_RE = re.compile(r'([一-龯々]+)\[([^\]]+)\]')

class FrenchLessonProcessor(BaseLessonProcessor):
    """
    Lesson processor for Tutorial module.
    Registers additional transformers specific to Tutorial lessons.
    """

    def __init__(self):
        from pathlib import Path

        BASE_DIR = Path(__file__).resolve().parents[1]

        DIR = BASE_DIR / "data" / "lessons"

        super().__init__(
            language = Languages.FRENCH.obj(),
            data_root = DIR
        )
    
_PROCESSOR: FrenchLessonProcessor | None = None

def get_processor() -> FrenchLessonProcessor:
    global _PROCESSOR
    if _PROCESSOR is None:
        _PROCESSOR = FrenchLessonProcessor()
    return _PROCESSOR
