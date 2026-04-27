import os
import re
from flask import Blueprint, abort, current_app, flash, jsonify, redirect, render_template, url_for
from lingual.modules.french.utils import quiz_utils
from lingual.modules.french.utils.lessons_processor import get_processor
from lingual.modules.french import GIT_FRENCH_DIRECTORY
from lingual.utils.languages import Languages

french_bp = Blueprint(
    Languages.FRENCH.obj().app_code,
    __name__,
    url_prefix=f"/{Languages.FRENCH.obj().app_code}",
    template_folder='templates',
    static_folder='static',
    static_url_path=f"/modules/{Languages.FRENCH.obj().app_code}/static"
)

VALID_SLUG = re.compile(r'^[a-zA-Z0-9\-]+$')

@french_bp.route('/')
def home():
    from lingual.utils.home_config import HomeConfig, HomeSection, HomeBanner, ItemBox

    config = HomeConfig()

    welcome_banner = HomeBanner("Welcome to the French module!")
    config.register_section(welcome_banner)

    quick_access = HomeSection("Quick Access")
    quick_access.add_items(
        ItemBox(
            title="Lessons",
            body="Start here for French content.",
            buttons=[
                ItemBox.BoxButton(
                text="Click here!",
                link=url_for('french.lessons')
                )
            ],
            on_click=url_for('french.lessons')
        )
    )

    config.register_section(quick_access)

    return render_template('french-home.html', config=config)

@french_bp.route('/lessons/')
@french_bp.route('/lessons/<slug>')
def lessons(slug=None):
    if slug and VALID_SLUG.match(slug):
        try:
            lesson_data = get_processor().load(slug)
        except FileNotFoundError:
            flash("Lesson not found.", "error")
            return redirect(url_for('french.lessons'))
        except Exception as e:
            current_app.logger.error(f"An error occurred while loading the lesson {slug}: {str(e)}")
            flash("An error occurred while loading the lesson.", "error")
            return redirect(url_for('french.lessons'))

        lesson_data['source_url'] = f"{GIT_FRENCH_DIRECTORY}/lessons/{slug}.md"

        return render_template(
            'french-lesson.html',
            lesson=lesson_data,
            data_root=lesson_data.get("data_root")
        )

    lessons = get_processor().get_lessons()
    return render_template('french-lesson-directory.html', lessons=lessons)


@french_bp.route('/lessons/api/quiz/<lesson_slug>', methods=['GET'], strict_slashes=False)
def get_quizzes(lesson_slug):
    # Validate slug to prevent directory traversal attacks
    if not lesson_slug or not VALID_SLUG.match(lesson_slug):
        abort(400, description="Invalid lesson slug.")

    base_dir = os.path.join(get_processor().data_root, 'quizzes')
    path = os.path.join(base_dir, f"{lesson_slug}.json")

    # Ensure the resolved path is still inside the quizzes directory
    if not os.path.realpath(path).startswith(os.path.realpath(base_dir)):
        abort(400, description="Invalid path.")

    try:
        data = quiz_utils.load_quiz_data(lesson_slug)
    except Exception:
        return jsonify({"error": "Malformed quiz JSON."}), 500

    if not data:
        return jsonify({"error": "Quiz not found."}), 404

    return jsonify(data)
