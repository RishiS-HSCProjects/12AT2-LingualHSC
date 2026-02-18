import os
import json
import requests
import unicodedata
from pathlib import Path
from enum import Enum

# Environment variable for WaniKani API Key
# todo: Allow users to input their own API key in the future
# for a more intergrated experience with their WaniKani account,
# and to avoid hitting rate limits on a shared API key.
WANIKANI_API_KEY = os.getenv("WANIKANI_API_KEY", None)

# Checker for API key validity.
CHECK_KEY = lambda: (_ for _ in ()).throw(KeyError("WANIKANI_API_KEY environment variable not set.")) if WANIKANI_API_KEY is None else None

# Base URL for the WaniKani Kanji API
API_URL = "https://api.wanikani.com/v2/subjects"

# Data directory where kanji information is stored locally
DATA_DIRECTORY = Path(__file__).parent.parent / "data" / "kanji"
DATA_DIRECTORY.mkdir(parents=True, exist_ok=True)

PRESCRIBED_KANJI = []  # List of kanji characters that are prescribed in the HSC syllabus

def validate_kanji(kanji: str) -> str:
    """
    Ensures the input is exactly one character and safe for use in URLs and filesystem paths.
    """

    if not isinstance(kanji, str):
        raise ValueError("Kanji must be a string.")

    if len(kanji) != 1:
        raise ValueError("Kanji must be exactly one character.")

    ch = kanji[0]

    # Reject whitespace, control chars, path separators, null byte
    if ch.isspace() or ch in {"/", "\\", "\x00"}:
        raise ValueError("Invalid character.")

    # Reject control characters (C0/C1)
    category = unicodedata.category(ch)
    if category.startswith("C"):
        raise ValueError("Invalid character.")

    return ch

class KanjiType(Enum):
    """Enum representing the types of kanji usage (e.g., ACTIVE or RECOGNITION)."""
    ACTIVE = 0  # Actively used kanji that students are expected to be able to read and write.
    RECOGNITION = 1  # Recognition-only kanji.
    PASSIVE = 2  # Non-standard type for kanji that are not part of the prescribed lists. Used as a catch-all for any kanji that doesn't fit into the other categories.

class ReadingType(Enum):
    """ Enum representing the reading type (onyomi or kunyomi) """
    ON = 'onyomi'
    KUN = 'kunyomi'

class Kanji:
    """Represents a Kanji character with associated information fetched from the WaniKani API."""

    def __init__(self, kanji_char: str, data: dict):
        """
        Initializes the Kanji object either with the provided data or by fetching it from the API
        
        Do not call this constructor directly if you want to get the kanji object with data.
        This constructor will always attempt to fetch data from the API if no data is provided,
        which can lead to unnecessary API calls and potential rate limiting.
        Instead, use the static method `get_kanji` which will handle data fetching and caching.
        """
        self.kanji_char: str = kanji_char
        self.data: dict = data

    @property
    def meanings(self) -> list:
        """Returns a list of meanings for the kanji."""
        return self.data.get("meanings", [])

    @property
    def readings(self) -> list:
        """Returns a list of readings for the kanji."""
        return self.data.get("readings", [])

    @property
    def stroke_count(self) -> int:
        """Returns the stroke count for the kanji."""
        return self.data.get("stroke_count", 0)

    def _get_readings_by_type(self, reading_type: str) -> list:
        """Filters readings based on the specified type (e.g., 'kun', 'on', 'nanori')."""
        return [reading for reading in self.readings if reading["type"] == reading_type]

    @property
    def kun_readings(self) -> list:
        """Returns the 'kun' readings of the kanji."""
        return self._get_readings_by_type(ReadingType.KUN.value)

    @property
    def on_readings(self) -> list:
        """Returns the 'on' readings of the kanji."""
        return self._get_readings_by_type(ReadingType.ON.value)
    
    @property
    def type(self) -> KanjiType:
        """ Returns the type of the kanji (ACTIVE, RECOGNITION, or PASSIVE). """
        type = self.data.get("type", KanjiType.PASSIVE.name).lower()
        return KanjiType(type) if type in KanjiType._value2member_map_ else KanjiType.PASSIVE

    def get_primary_meaning(self) -> str:
        """
        Retrieves the primary meaning of the kanji.
        """
        for meaning in self.meanings:
            if meaning.get("primary"):
                return meaning.get("meaning", "")
        return ""

    @staticmethod
    def _fetch_kanji_data(kanji: str) -> dict:
        """
        Fetches kanji data from the WaniKani API and stores it locally.
        """

        CHECK_KEY()  # Ensure API key is set

        kanji = validate_kanji(kanji)

        response = requests.get(
            API_URL,
            headers={"Authorization": f"Bearer {WANIKANI_API_KEY}"},
            params={"types": "kanji", "slugs": kanji},  # safer than URL formatting
            timeout=10
        )

        if not response.ok:
            raise Exception(f"Kanji request failed ({response.status_code}) for '{kanji}'.")

        data = response.json()

        if "data" not in data or not data["data"]:
            raise Exception(f"No data found for kanji '{kanji}'.")

        # Extract the first subject object
        subject = data["data"][0]

        # Extract the actual kanji data dictionary
        kanji_data = subject["data"]

        file_path = DATA_DIRECTORY / f"{kanji}.json"
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(kanji_data, file, ensure_ascii=False, indent=4)

        return kanji_data

    @staticmethod
    def get_kanji(kanji: str) -> "Kanji":
        """
        Retrieves a Kanji object, fetching data if not cached.
        """

        kanji = validate_kanji(kanji) # Set kanji to validated character
        file_path = DATA_DIRECTORY / f"{kanji}.json"

        if Kanji.is_cache_available(kanji):
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)
        else:
            data = Kanji._fetch_kanji_data(kanji)

        return Kanji(kanji, data)

    @staticmethod
    def is_cache_available(kanji: str) -> bool:
        """
        Checks if data for the specified kanji is already available locally.
        """
        kanji = validate_kanji(kanji) # Set kanji to validated character
        file_path = DATA_DIRECTORY / f"{kanji}.json"
        return file_path.exists()

    @staticmethod
    def get_prescribed_kanji() -> list[tuple[str, KanjiType]]:
        """
        Returns a list of kanji prescribed for study in the Japanese school system.
        """
        global PRESCRIBED_KANJI # Bad approach but it allows us to cache the prescribed kanji list in memory
                                # after the first load, which is a significant performance improvement since
                                # this list is accessed frequently and doesn't change during runtime.

        if not PRESCRIBED_KANJI:
            with open(DATA_DIRECTORY / "prescribed_kanji.json", "r", encoding="utf-8") as file:
                data = json.load(file) # Get the raw data as a dictionary of kanji to type mappings
            PRESCRIBED_KANJI = [(kanji, KanjiType(type_)) for kanji, type_ in data.items()] # Convert to a list of tuples containing the kanji character and its corresponding type as a KanjiType enum member
        
        return PRESCRIBED_KANJI

    def __str__(self):
        """Returns a string representation of the Kanji object."""
        primary_meaning = self.get_primary_meaning()
        primary_reading = self.on_readings[0]["reading"] if self.on_readings else "N/A"
        return f"Kanji: {self.kanji_char}, Meaning: {primary_meaning}, Primary Reading: {primary_reading}, Stroke Count: {self.stroke_count}"
