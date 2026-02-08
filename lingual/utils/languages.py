import json
from enum import Enum

class Language:
    def __init__(
            self,
            code: str,
            name: str,
            native_name: str,
            app_code: str,
            app_name: str
        ):
        self.code = code
        self.name = name
        self.native_name = native_name
        self.app_code = app_code
        self.app_name = app_name

    def __repr__(self) -> str:
        return f"Language(code={self.code!r}, name={self.name!r}, native_name={self.native_name!r}, app_code={self.app_code!r}, app_name={self.app_name!r})"

class Languages(Enum):
    JAPANESE = Language(code='jp', name='Japanese', native_name='日本語', app_code='nihongo', app_name='日本Go!')

    def obj(self) -> Language:
        return self.value

    @classmethod
    def get_language_by_code(cls, code: str) -> Language | None:
        for lang in cls:
            if lang.value.code == code:
                return lang.value
        return None

_TRANSLATABLES = None
def _load_translatables() -> dict:
    """
    Load translatable strings from JSON file once and cache them in memory.
    This makes accessing translatable strings more efficient by avoiding 
    repeatedly opening and reading the file.
    """
    global _TRANSLATABLES
    if _TRANSLATABLES is None:
        with open('lingual/utils/translatable.json', 'r', encoding='utf-8') as f:
            _TRANSLATABLES = json.load(f)
    return _TRANSLATABLES

def get_translatable(language_code: str, key: str) -> str:
    try:
        translatables = _load_translatables()

        if key not in translatables:
            raise KeyError(f"Translatable key '{key}' not found.")

        translations = translatables[key]

        # Try requested language
        if language_code in translations:
            return translations[language_code]

        # Fallback to English
        return translations.get("en", "Translation not available.")

    except Exception as e:
        from flask import current_app
        current_app.logger.error(f"Error loading translatable data for key '{key}' on language '{language_code}': {e}")
        return "ERROR"
