from pathlib import Path
from functools import lru_cache
from flask import url_for
import frontmatter
import markdown
import re
from lingual.utils.languages import Language

MARKDOWN_EXTENSIONS = [
    "extra",
    "tables",
    "fenced_code",
    "toc",
    "attr_list",
    "md_in_html",
]

# REGEXE PATTERNS
LINK_RE = re.compile(r'\[([^\]]+)\]\((\w+):([\w\-]+)\)')
QUIZ_RE = re.compile(r'~quizzes:([\w\-]+):([\w\-]+)(?:\?([^\~]+))?~')
NOTE_RE = re.compile(r'/i\s+(.*?)\\', re.DOTALL)
WARNING_RE = re.compile(r'/w\s+(.*?)\\', re.DOTALL)
COLOR_RE = re.compile(r'::([a-zA-Z]+|#[0-9a-fA-F]{3,6})\{([^}]+)\}')

class BaseLessonProcessor:
    """
    Base processor for all languages.
    Languages extend this by registering extra transformers.
    """


    def __init__(self, language: Language, data_root: Path):
        self.language: Language = language
        self.data_root: Path = data_root
        self.transformers = [ # Languages will extend this list
            self.transform_links,
            self.transform_quizzes,
            self.transform_notes,
            self.transform_color,
        ]

    def transform_links(self, text: str) -> str:
        def repl(match):
            label = match.group(1)
            route = match.group(2)
            slug = match.group(3)

            return f'<a href="{url_for(f"{self.language.app_code}.{route}", slug=slug)}">{label}</a>'

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
        text = NOTE_RE.sub(
            r'<div class="note"><strong>Note:</strong><p>\1</p></div>', text
        )
        text = WARNING_RE.sub(
            r'<div class="warning"><strong>Warning:</strong><p>\1</p></div>', text
        )
        return text
    
    def transform_color(self, text: str) -> str:
        return COLOR_RE.sub(
            r'<span style="color:\1">\2</span>',
            text
        )


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

    # @lru_cache(maxsize=128)
    def load(self, slug: str) -> dict:
        path = self.data_root / "lessons" / f"{slug}.md"
        if not path.exists():
            raise FileNotFoundError(f"Lesson not found: {path}")

        post = frontmatter.load(path)  # Separates YAML metadata from MD content
        content = self.apply_transforms(post.content)  # Applies custom transformations

        # Convert MD to HTML
        html = markdown.markdown( 
            content,
            extensions=MARKDOWN_EXTENSIONS,  # Install extensions
            output_format="html5",           # HTML5 output
        )

        return {
            "meta": post.metadata,  # YAML metadata
            "content": html,        # HTML content
            "slug": slug,           # Lesson slug
            "data_root": self.data_root,
        }
