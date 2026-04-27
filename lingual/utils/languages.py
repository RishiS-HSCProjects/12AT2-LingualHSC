import json
from enum import Enum

class Language:
    def __init__(
            self,
            code: str,          # Unique language code (e.g. 'en', 'jp').
            name: str,          # English name of the language (e.g. 'English', 'Japanese').
            native_name: str,   # Native name of the language (e.g. 'English', '日本語').
            app_code: str,      # Code used in the app to identify the language (e.g. 'english', 'nihongo').
            app_name: str       # Name of the language as displayed in the app (e.g. 'English', '日本Go!').
        ):
        self.code = code
        self.name = name
        self.native_name = native_name
        self.app_code = app_code
        self.app_name = app_name

    def __repr__(self) -> str:
        # Custom repr for easier debugging and logging.
        # `!r` ensures that the output is 'unambiguous' and includes quotes around strings.
        return f"Language(code={self.code!r}, name={self.name!r}, native_name={self.native_name!r}, app_code={self.app_code!r}, app_name={self.app_name!r})"

class Languages(Enum):
    # Register languages here.
    TUTORIAL = Language(code='xx', name='Tutorial', native_name='xx', app_code='tutorial', app_name='Tutorial')
    JAPANESE = Language(code='jp', name='Japanese', native_name='日本語', app_code='nihongo', app_name='日本Go!')
    FRENCH   = Language(code='fr', name='French', native_name='le français', app_code='french', app_name='French')

    def obj(self) -> Language:
        """ Returns the Language object associated with the enum member. """
        return self.value

    @classmethod
    def get_languages(cls):
        """ Returns a list of all registered Language objects, excluding the tutorial. """
        return [lang.obj() for lang in Languages if lang is not Languages.TUTORIAL]
    
    @classmethod
    def get_language_by_code(cls, code: str) -> Language | None:
        for lang in cls:
            if lang.value.code == code:
                return lang.obj()
        return None
    
    @classmethod
    def get_language_by_app_code(cls, app_code: str) -> Language | None:
        for lang in cls:
            if lang.value.app_code == app_code:
                return lang.obj()
        return None

# Global variable to cache translatable strings loaded from JSON file for efficient access.
_TRANSLATABLES = None

def _load_translatables() -> dict:
    """
    Load translatable strings from JSON file once and cache them in memory.
    This makes accessing translatable strings more efficient by avoiding 
    repeatedly opening and reading the file.
    """
    global _TRANSLATABLES
    if _TRANSLATABLES is None:
        # First load - read from file and cache in memory.
        with open('lingual/utils/translatable.json', 'r', encoding='utf-8') as f:
            _TRANSLATABLES = json.load(f) # Cache the loaded translatables in the global variable for future access.
    return _TRANSLATABLES # Return the cached translatables for subsequent calls.

def get_translatable(language_code: str, key: str) -> str:
    """ Retrieve a translatable string for a given language code and key, with fallback to English if the specific language translation is not available. """
    try:
        translatables = _load_translatables()

        if key not in translatables:
            raise KeyError(f"Translatable key '{key}' not found.")

        translations = translatables[key]

        # Try requested language
        if language_code in translations:
            return translations[language_code] # Return translation

        # Fallback to English
        return translations.get("en", "Translation not available.")

    except KeyError as e:
        from flask import current_app
        current_app.logger.warning(f"Missing/unknown translatable key '{key}': {e}")
    except Exception as e:
        from flask import current_app
        current_app.logger.error(f"Error loading translatable data for key '{key}' on language '{language_code}': {e}")
    
    return "TRANSLATION_ERROR" # Return a default error string if something goes wrong.
