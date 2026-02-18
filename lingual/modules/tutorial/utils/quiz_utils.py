import json
from pathlib import Path
from .lessons_processor import get_processor

def load_quiz_data(lesson_slug: str) -> dict | None:
    base_dir = Path(get_processor().data_root) / "quizzes"
    path = base_dir / f"{lesson_slug}.json"

    if not path.exists():
        return None

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    return data
