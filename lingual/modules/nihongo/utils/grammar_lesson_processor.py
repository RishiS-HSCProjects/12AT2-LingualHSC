import re
from lingual.utils.languages import Languages
from lingual.utils.lesson_processor import BaseLessonProcessor

FURIGANA_RE = re.compile(r'([一-龯々]+)\[([^\]]+)\]') # Regex to match Kanji[kana] patterns for furigana transformation

class NihongoLessonProcessor(BaseLessonProcessor):
    """
    Lesson processor for Nihongo module.
    Registers additional transformers specific to Japanese lessons.
    """

    def __init__(self):
        from pathlib import Path

        # Go up 3 levels: grammar → utils → nihongo
        BASE_DIR = Path(__file__).resolve().parents[1]

        DIR = BASE_DIR / "data" / "grammar" # Directory containing grammar lesson data

        super().__init__(
            language = Languages.JAPANESE.obj(),
            data_root = DIR
        ) # Initialise superclass with Japanese language and grammar data directory

        self.add_transform(self.transform_furigana)

    # Transformers
    def transform_furigana(self, text: str) -> str:
        """ Convert Kanji[kana] to ruby HTML tags for furigana display.

        Example: `漢字[かんじ]` → `<ruby>漢字<rt>かんじ</rt></ruby>`
        """
        return FURIGANA_RE.sub(r'<ruby>\1<rt>\2</rt></ruby>', text)
    
_PROCESSOR: NihongoLessonProcessor | None = None # Singleton instance of the lesson processor, initially None

def get_processor() -> NihongoLessonProcessor:
    """ Factory function to get the singleton instance of NihongoLessonProcessor. """
    # Singleton pattern to ensure only one instance of the processor is created
    global _PROCESSOR
    if _PROCESSOR is None:
        _PROCESSOR = NihongoLessonProcessor()
    return _PROCESSOR
