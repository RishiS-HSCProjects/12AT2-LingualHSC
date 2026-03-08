import json
import re
from pathlib import Path
from typing import Any

import bleach
import markdown

from lingual.utils.tiles_utils import TileSection

SIMPLE_MD_EXTENSIONS = [
    "extra",
    "tables",
    "fenced_code",
    "sane_lists",
    "nl2br",
]

SAFE_TAGS = list(bleach.sanitizer.ALLOWED_TAGS) + [
    "p",
    "br",
    "hr",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "pre",
    "code",
    "blockquote",
    "ul",
    "ol",
    "li",
    "table",
    "thead",
    "tbody",
    "tr",
    "th",
    "td",
]

SAFE_ATTRIBUTES = {
    "*": ["class"],
    "a": ["href", "title", "target", "rel"],
    "code": ["class"],
}


class ParticleTilesProcessor:
    def __init__(self, data_root: Path | None = None):
        self.data_root = data_root or Path(__file__).resolve().parent.parent / "data" / "particles"
        self._index_cache: dict[str, Any] | None = None

    def _validate_slug(self, slug: str) -> str:
        if not re.fullmatch(r"[A-Za-z0-9\-]+", slug):
            raise ValueError("Invalid particle slug.")
        return slug

    def _read_index(self) -> dict[str, Any]:
        if self._index_cache is None:
            index_path = self.data_root / "map.json"
            with index_path.open("r", encoding="utf-8") as file:
                self._index_cache = json.load(file)
        return self._index_cache or {}

    def build_tile_section(self) -> TileSection:
        index = self._read_index()
        section = TileSection(
            id="particles",
            title=index.get("title", "Japanese Particles"),
            description=index.get("description", "Tap a particle to open notes."),
        )

        for category in index.get("categories", []):
            category_name = category.get("name", "")
            for item in category.get("items", []):
                slug = self._validate_slug(str(item.get("slug", "")))
                section.add_tile(
                    value=slug,
                    category=category_name,
                    label=item.get("tile", slug),
                    payload={
                        "tile": item.get("tile", slug),
                        "title": item.get("title", slug),
                    },
                )

        return section

    def _find_item_by_slug(self, slug: str) -> dict[str, Any] | None:
        index = self._read_index()
        for category in index.get("categories", []):
            category_name = category.get("name", "")
            for item in category.get("items", []):
                if str(item.get("slug", "")) == slug:
                    item_copy = dict(item)
                    item_copy["category"] = category_name
                    return item_copy
        return None

    def _render_markdown(self, content: str) -> str:
        html = markdown.markdown(content, extensions=SIMPLE_MD_EXTENSIONS, output_format="html")
        return bleach.clean(
            html,
            tags=SAFE_TAGS,
            attributes=SAFE_ATTRIBUTES,
            protocols=["http", "https", "mailto"],
            strip=True,
        )

    def load_particle(self, slug: str) -> dict[str, Any]:
        slug = self._validate_slug(slug)
        item = self._find_item_by_slug(slug)
        if item is None:
            raise FileNotFoundError(f"Particle not found in map: {slug}")

        markdown_path = self.data_root / "notes" / f"{slug}.md"
        if not markdown_path.exists():
            raise FileNotFoundError(f"Particle markdown not found: {slug}")

        content = markdown_path.read_text(encoding="utf-8")
        html = self._render_markdown(content)

        return {
            "slug": slug,
            "tile": item.get("tile", slug),
            "title": item.get("title", slug),
            "category": item.get("category", ""),
            "content_html": html,
        }
