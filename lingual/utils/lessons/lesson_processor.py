from dataclasses import dataclass
from pathlib import Path
from functools import lru_cache
from flask import current_app, url_for
import frontmatter
import markdown
import re
from lingual.utils.languages import Language
from werkzeug.routing import BuildError
from markupsafe import escape

MARKDOWN_EXTENSIONS = [
    "extra",
    "tables",
    "fenced_code",
    "toc",
    "attr_list",
    "md_in_html",
]

# REGEX PATTERNS
LINK_RE = re.compile(r'\[([^\]]+)\]\((\w+):([\w\-]+)(?:#([\w\-]+))?\)') # [label](route:slug#anchor) Optional anchor
QUIZ_RE = re.compile(r'~quizzes:([\w\-]+):([\w\-]+)(?:\?([^\~]+))?~') # ~quizzes:lesson:quiz?param1=value1&param2=value2~
NOTE_RE = re.compile(r'/([iwt])\s+(.*?)\\', re.DOTALL) # /type text\, either i (info), w (warning), t (tip)
FORMAT_RE = re.compile(r'::([a-zA-Z]+|#[0-9a-fA-F]{3,6})\{([^}]+)\}') # ::color{text} / ::bold/italic{text}
BLOCK_RE = re.compile(r':::(\w+)\s+(.*?):::', re.DOTALL) # :::type ... :::, either blockquote or warning.
SPOILER_RE = re.compile(r'\|\|(.*?)\|\|', re.DOTALL) # ||spoiler content||

class BaseLessonProcessor:
    """
    Base processor for all languages.
    Languages extend this by registering extra transformers.
    """

    def __init__(self, language: Language, data_root: Path):
        self.language: Language = language
        self.data_root: Path = data_root
        self.transformers = [ # Languages can add on to this list
            self.transform_links,
            self.transform_quizzes,
            self.transform_notes,
            self.transform_formatting,
            self.transform_blocks,
            self.transform_spoilers,
        ]

    def transform_links(self, text: str) -> str:
        def repl(match):
            label = match.group(1)
            route = match.group(2)
            slug = match.group(3)
            anchor = match.group(4)

            try:
                href = url_for(f"{self.language.app_code}.{route}", slug=slug) # Build URL for route
                if anchor: href += f"#{anchor}" # Append anchor if present
            except BuildError:
                # In case of BuildError, fallback to empty URL and log warning
                href = "#"
                current_app.logger.warning(f"Failed to build URL for route '{route}' with slug '{slug}'")

            return f'<a href="{href}">{label}</a>' # Return HTML anchor tag

        return LINK_RE.sub(repl, text)

    def transform_quizzes(self, text: str) -> str:
        def repl(match):
            lesson, quiz, params = match.groups() # Separates str into a tuple including lesson, quiz, and params
            attrs = "" # Additional data attributes
            if params:
                for param in params.split("&"):
                    if "=" in param:
                        key, value = param.split("=", 1)
                        attrs += f' data-{key}="{value}"' # Key-value attribute
                    else:
                        attrs += f' data-{param}="true"' # Boolean attribute
            return f'<div class="quiz" data-lesson="{lesson}" data-id="{quiz}"{attrs}></div>' # Quiz content dynamically loaded via JS

        return QUIZ_RE.sub(repl, text)

    def transform_notes(self, text: str) -> str:
        def repl(match):
            note_type = match.group(1)
            content = match.group(2)

            mapping = {
                "i": ("info", "Info"),
                "w": ("warning", "Warning"),
                "t": ("tip", "Tip"),
            }

            css_class, label = mapping.get(note_type, ("info", "Note"))

            return f'\n<div class="note {css_class}"><strong class="label">{label}:</strong><p>{content}</p></div>\n'

        return NOTE_RE.sub(repl, text)
    
    def transform_formatting(self, text: str):
        def repl(match):
            formatting = match.group(1)
            content = match.group(2)

            # Handle formatting while parsing "escaped" content to prevent XSS
            if formatting.lower() == "bold":
                return f'<strong>{escape(content)}</strong>'
            elif formatting.lower() == "italic":
                return f'<em>{escape(content)}</em>'

            return f'<span style="color:{formatting}">{escape(content)}</span>' # Assume colour

        return FORMAT_RE.sub(repl, text)

    def transform_blocks(self, text: str) -> str:
        def repl(match):
            block_type = match.group(1)
            content = match.group(2)
            return f'<div class="block {block_type}">{content}</div>'

        return BLOCK_RE.sub(repl, text)
    
    def transform_spoilers(self, text: str) -> str:
        def repl(match):
            content = match.group(1)
            return f'<span class="spoiler" title="Click to reveal">{content}</span>'
        return SPOILER_RE.sub(repl, text)

    def add_transform(self, transform) -> None:
        """
        Languages call this to register new transformations.

        :param transform: Callable that takes and returns a string.
        """
        self.transformers.append(transform)

    def apply_transforms(self, content: str) -> str:
        for transform in self.transformers:
            content = transform(content)
        return content

    # Cache up to 16 lessons in memory for performance
    # Has the issue of not updating if lesson files change on disk,
    # however, a "cache clear" mechanism can be implemented later.
    # @lru_cache(maxsize=16) todo: enable
    def load(self, slug: str) -> dict:
        if not re.fullmatch(r"[A-Za-z0-9\-]+", slug):
            raise ValueError("Invalid lesson slug.")

        path = self.data_root / "lessons" / f"{slug}.md"
        if not path.exists():
            raise FileNotFoundError(f"Lesson not found: {path}")

        post = frontmatter.load(path) # type: ignore -> Separates YAML metadata from MD content
        content = self.apply_transforms(post.content)  # Applies custom transformations

        # Convert MD to HTML
        html = markdown.markdown( 
            content,
            extensions=MARKDOWN_EXTENSIONS,  #                 Install extensions
            output_format="html5",           # type: ignore -> HTML5 output
        )

        return {
            "meta": post.metadata,  # YAML metadata
            "content": html,        # HTML content
            "slug": slug,           # Lesson slug
            "data_root": self.data_root,
        }

    def get_lessons(self) -> list[dict[str, list["Lesson"]]]:
        lesson_slugs_path = self.data_root / "map.json"

        if lesson_slugs_path.exists():
            import json
            with open(lesson_slugs_path, "r", encoding="utf-8") as f:
                slug_data = json.load(f)
        else:
            slug_data = {}

        categories: list[dict[str, list["Lesson"]]] = []

        for category_name, slugs in slug_data.items(): # Iterate through each category
            category_lessons: list[Lesson] = [] # Lessons in this category

            for slug in slugs:
                try:
                    # Load just the metadata and raw markdown content for search
                    lesson_path = self.data_root / "lessons" / f"{slug}.md"
                    if not lesson_path.exists():
                        current_app.logger.warning(
                            f"Lesson file '{slug}' not found in category '{category_name}'."
                        )
                        continue
                    
                    post = frontmatter.load(lesson_path)  # type: ignore
                    meta = post.metadata

                    if meta is None:
                        current_app.logger.warning(
                            f"Lesson '{slug}' in category '{category_name}' is missing metadata."
                        )
                        continue

                    # Run title & summary through the same transformation pipeline
                    title_raw = meta.get("title", "Untitled")
                    summary_raw = meta.get("summary", "")

                    title = self.apply_transforms(title_raw) # type: ignore -> Transform title
                    summary = self.apply_transforms(summary_raw) # type: ignore -> Transform summary
                    
                    # Get plain text content directly from markdown (before HTML conversion)
                    # Only extract content from within :::blockquote, :::warning, and similar blocks                    
                    content_plain = ""
                    raw_content = post.content
                    
                    # Extract content within ::: blocks (blockquote, warning, etc.)
                    block_pattern = r':::(?:blockquote|warning|note|tip)\s+(.*?):::'
                    matches = re.findall(block_pattern, raw_content, re.DOTALL)
                    
                    for match in matches:
                        # Clean up the extracted content
                        cleaned = match
                        # Remove custom markers like /i, /t, /w
                        cleaned = re.sub(r'/[itwb]\s+', '', cleaned)
                        # Remove color/formatting markers like ::blue{}, ::green{}
                        cleaned = re.sub(r'::[a-z]+\{([^}]*)\}', r'\1', cleaned)
                        # Remove ruby/furigana brackets but keep text
                        cleaned = re.sub(r'\[([^\]]+)\]', r'\1', cleaned)
                        # Remove markdown links but keep text
                        cleaned = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', cleaned)
                        # Remove markdown formatting
                        cleaned = re.sub(r'[*_`#]', '', cleaned)
                        
                        content_plain += " " + cleaned
                    
                    # Normalize whitespace
                    content_plain = re.sub(r'\s+', ' ', content_plain).strip()

                    category_lessons.append(
                        Lesson(
                            slug=slug,
                            title=title,
                            summary=summary,
                            content=content_plain,
                        )
                    )
                except Exception as e:
                    current_app.logger.warning(
                        f"Failed to load lesson '{slug}' in category '{category_name}': {str(e)}"
                    )

            categories.append({
                "category": category_name,
                "lessons": category_lessons
            })

        return categories

@dataclass
class Lesson:
    slug: str
    title: str
    summary: str
    content: str = ""
