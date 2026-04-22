import json
import re
from pathlib import Path
from typing import Any

import bleach
import markdown

from lingual.utils.tiles_utils import TileSection

SIMPLE_MD_EXTENSIONS = [ # Basic markdown extensions for simple formatting in particle notes
    "extra",
    "tables",
    "fenced_code",
    "sane_lists",
    "nl2br",
]

SAFE_TAGS = list(bleach.sanitizer.ALLOWED_TAGS) + [ # Allow basic HTML tags for formatting in particle notes, in addition to bleach's default allowed tags
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

SAFE_ATTRIBUTES = { # Define safe attributes for HTML tags in particle notes
    "*": ["class"],
    "a": ["href", "title", "target", "rel"],
    "code": ["class"],
}

class ParticleTilesProcessor:
    """ Processor for building particle tiles and loading particle notes. """
    def __init__(self, data_root: Path | None = None):
        self.data_root = data_root or Path(__file__).resolve().parent.parent / "data" / "particles"
        self._index_cache: dict[str, Any] | None = None

    def _validate_slug(self, slug: str) -> str:
        """ Validate that the slug is a simple alphanumeric string with optional dashes, to prevent path traversal or invalid filenames. """
        if not re.fullmatch(r"[A-Za-z0-9\-]+", slug):
            raise ValueError("Invalid particle slug.")
        return slug # Return the validated slug for further processing

    def _read_index(self) -> dict[str, Any]:
        """ Read and cache the index file (map.json) that contains metadata about particles and their categorisation. """
        if self._index_cache is None:
            index_path = self.data_root / "map.json"
            with index_path.open("r", encoding="utf-8") as file:
                self._index_cache = json.load(file)
        return self._index_cache or {}

    def build_tile_section(self) -> TileSection:
        """ Build a TileSection object based on the index data, which will be used to display the particle tiles in the UI. """
        index = self._read_index()
        section = TileSection(
            id="particles",
            title=index.get("title", "Japanese Particles"),
            description=index.get("description", "Tap a particle to open notes."),
        )

        for category in index.get("categories", []): # Iterate through each category in the index to build the tile section
            category_name = category.get("name", "")
            for item in category.get("items", []): # Iterate through each particle item in the category to add tiles to the section
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
        """ Find a particle item by its slug. """
        index = self._read_index() # Read the index to access the categories and items for lookup
        for category in index.get("categories", []):
            category_name = category.get("name", "")
            for item in category.get("items", []): # Iterate through each particle item in the category
                if str(item.get("slug", "")) == slug:
                    item_copy = dict(item) # Create a fresh copy of the item to avoid mutating the original index data
                    item_copy["category"] = category_name
                    return item_copy # Return the found item with its category added, or None if not found after iterating through all categories and items
        return None

    def _render_markdown(self, content: str) -> str:
        """ Basic markdown rendering with bleach sanitisation to ensure safe HTML output for particle notes. """
        # TODO: Use lesson processor transformers for consistency and greater rendering capabilities (e.g. furigana support)
        html = markdown.markdown(content, extensions=SIMPLE_MD_EXTENSIONS, output_format="html")
        return bleach.clean(
            html,
            tags=SAFE_TAGS,
            attributes=SAFE_ATTRIBUTES,
            protocols=["http", "https", "mailto"],
            strip=True,
        )

    def load_particle(self, slug: str) -> dict[str, Any]:
        """ Load the particle notes content based on the slug, and return a dictionary containing the particle's metadata and rendered HTML content. """
        slug = self._validate_slug(slug)
        item = self._find_item_by_slug(slug)
        if item is None:
            raise FileNotFoundError(f"Particle not found in map: {slug}")

        markdown_path = self.data_root / "notes" / f"{slug}.md"
        if not markdown_path.exists():
            raise FileNotFoundError(f"Particle markdown not found: {slug}")

        content = markdown_path.read_text(encoding="utf-8")
        html = self._render_markdown(content)

        return { # Return a dictionary containing the particle's slug, tile label, title, category, and rendered HTML content for use in the UI
            "slug": slug,
            "tile": item.get("tile", slug),
            "title": item.get("title", slug),
            "category": item.get("category", ""),
            "content_html": html,
        }
