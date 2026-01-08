import json
from enum import Enum

class Language:
    def __init__(
            self,
            code: str,
            name: str,
            native_name: str,
            app_name: str
        ):
        self.code = code
        self.name = name
        self.native_name = native_name
        self.app_name = app_name

    def __repr__(self) -> str:
        return f"Language(code='{self.code}', name='{self.name}', native_name='{self.native_name}')"


class Languages(Enum):
    JAPANESE = Language('jp', 'Japanese', '日本語', 'nihongo')

    def obj(self) -> Language:
        return self.value

    @classmethod
    def get_language_by_code(cls, code: str) -> Language | None:
        for lang in cls:
            if lang.value.code == code:
                return lang.value
        return None

def get_translatable(language_code: str, key: str) -> str:
    try:
        with open('lingual/utils/translatable.json', 'r', encoding='utf-8') as f:
            translatables = json.load(f)

        if key not in translatables:
            raise KeyError(f"Translatable key '{key}' not found.")

        translations = translatables[key]

        # Try requested language
        if language_code in translations:
            return translations[language_code]

        # Fallback to English
        return translations.get("en")

    except Exception as e:
        print(f"Error loading translatable data for key '{key}' on language '{language_code}': {e}")
        return "ERROR"
