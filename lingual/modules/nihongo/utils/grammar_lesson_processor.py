import re
from lingual.utils.languages import Languages
from lingual.utils.lessons.lesson_processor import BaseLessonProcessor

FURIGANA_RE = re.compile(r'([一-龯々]+)\[([^\]]+)\]')

class NihongoLessonProcessor(BaseLessonProcessor):
    """
    Lesson processor for Nihongo module.
    Registers additional transformers specific to Japanese lessons.
    """

    def __init__(self):
        from pathlib import Path

        # Go up 3 levels: grammar → utils → nihongo
        BASE_DIR = Path(__file__).resolve().parents[1]

        DIR = BASE_DIR / "data" / "grammar"

        from flask import current_app
        current_app.logger.debug(DIR)

        super().__init__(
            language = Languages.JAPANESE.obj(),
            data_root = DIR
        )

        self.add_transform(self.transform_furigana)

    # Transformers
    def transform_furigana(self, text: str) -> str:
        """ Convert Kanji[kana] to ruby HTML tags for furigana display.
        Example: 漢字[かんじ] -> <ruby>漢字<rt>かんじ</rt></ruby>
        """
        return FURIGANA_RE.sub(r'<ruby>\1<rt>\2</rt></ruby>', text)
    
_PROCESSOR: NihongoLessonProcessor | None = None

def get_processor() -> NihongoLessonProcessor:
    global _PROCESSOR
    if _PROCESSOR is None:
        _PROCESSOR = NihongoLessonProcessor()
    return _PROCESSOR
