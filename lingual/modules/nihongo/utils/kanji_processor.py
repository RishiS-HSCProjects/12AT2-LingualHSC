import os
import json
import requests
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
API_URL = "https://api.wanikani.com/v2/subjects?types=kanji&slugs={kanji}"

# Data directory where kanji information is stored locally
DATA_DIRECTORY = Path(__file__).parent.parent / "data" / "kanji"
DATA_DIRECTORY.mkdir(parents=True, exist_ok=True)


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
    def nanori_readings(self) -> list:
        """Returns the 'nanori' readings of the kanji."""
        return self._get_readings_by_type("nanori")

    def get_primary_meaning(self) -> str:
        """
        Retrieves the primary meaning of the kanji.

        Returns:
            str: The primary meaning, or an empty string if none is found.
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

        CHECK_KEY() # Ensure API key is set

        response = requests.get(
            API_URL.format(kanji=kanji), # Use formatted URL to query specific kanji
            headers={"Authorization": f"Bearer {WANIKANI_API_KEY}"}, # Add API key
            timeout=10 # Timeout to prevent hanging if the API is unresponsive.
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
    def get_cached_kanji(kanji: str) -> "Kanji":
        """
        Retrieves a cached Kanji object without hitting the API.
        """

        file_path = DATA_DIRECTORY / f"{kanji}.json"

        if not Kanji.is_cache_available(kanji):
            raise FileNotFoundError(f"Kanji '{kanji}' not cached")

        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        return Kanji(kanji, data)

    @staticmethod
    def get_kanji(kanji: str) -> "Kanji":
        """
        Retrieves a Kanji object, fetching data if not cached.
        """

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
        file_path = DATA_DIRECTORY / f"{kanji}.json"
        return file_path.exists()

    @staticmethod
    def get_prescribed_kanji() -> list:
        """
        Returns a list of kanji prescribed for study in the Japanese school system.
        """
        with open(DATA_DIRECTORY / "prescribed_kanji.json", "r", encoding="utf-8") as file:
            data = json.load(file)
        return [(kanji, KanjiType(type_)) for kanji, type_ in data.items()]

    def __str__(self):
        """Returns a string representation of the Kanji object."""
        primary_meaning = self.get_primary_meaning()
        primary_reading = self.on_readings[0]["reading"] if self.on_readings else "N/A"
        return f"Kanji: {self.kanji_char}, Meaning: {primary_meaning}, Primary Reading: {primary_reading}, Stroke Count: {self.stroke_count}"

class KanjiType(Enum):
    """Enum representing the types of kanji usage (e.g., ACTIVE or RECOGNITION)."""
    ACTIVE = 0 # Actively used kanji that students are expected to be able to read and write.
    RECOGNITION = 1 # Recognition-only kanji.
    PASSIVE = 2 # Non-standard type for kanji that are not part of the prescribed lists.

class ReadingType(Enum):
    """ Enum representing the reading type (onyomi or kunyomi) """
    ON = 'onyomi'
    KUN = 'kunyomi'
