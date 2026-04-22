import json
from pathlib import Path
from .lessons_processor import get_processor

def load_quiz_data(lesson_slug: str) -> dict | None:
    """ Loads quiz data for a given lesson slug. Returns the transformed quiz data or None if the file doesn't exist. """
    base_dir = Path(get_processor().data_root) / "quizzes" # Base directory for quizzes is a subdirectory of the lessons data root
    path = base_dir / f"{lesson_slug}.json" # Construct the path to the quiz data file based on the lesson slug

    if not path.exists():
        return None

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f) # Load the raw quiz data from the JSON file

    return get_processor().transform_data(data) # Use the lesson processor's transform_data method to convert raw MD into HTML
