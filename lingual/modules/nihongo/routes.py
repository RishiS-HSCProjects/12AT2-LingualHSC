import os
import re
from flask import Blueprint, abort, current_app, flash, json, jsonify, redirect, render_template, session, url_for
from flask_login import current_user, login_required
from lingual.utils.languages import Languages
from lingual.modules.nihongo.utils.lesson_processor import get_processor
from lingual.utils.lessons.lesson_processor import Lesson

nihongo_bp = Blueprint(
    Languages.JAPANESE.obj().app_code,
    __name__,
    url_prefix='/nihongo',
    template_folder='templates',
    static_folder='static',
    static_url_path='/modules/nihongo/static'
)

VALID_SLUG = re.compile(r'^[a-zA-Z0-9\-]+$')

@nihongo_bp.route('/')
@login_required
def home():
    from lingual.utils.home_config import HomeConfig, HomeSection, HomeBanner, ItemBox
    from lingual.utils.languages import get_translatable

    config = HomeConfig()

    welcome_banner = HomeBanner(get_translatable('jp', 'home_welcome_text').replace("{first_name}", current_user.first_name))
    config.register_section(welcome_banner)

    quick_access = HomeSection("Quick Access")

    quick_access.add_items(
        ItemBox(
            title="Grammar",
            body="Practise Practise Practise",
            buttons=[
                ItemBox.BoxButton(
                text="Learn",
                link=url_for('nihongo.grammar')
                ),
                ItemBox.BoxButton(
                    text="Quiz",
                    link=url_for('nihongo.grammar')
                )
            ],
            on_click=url_for('nihongo.grammar')
        ),
        ItemBox(
            title="Vocab",
            body="yes Yes yes",
            buttons=[
                ItemBox.BoxButton(
                text="Learn",
                link="#"
                ),
                ItemBox.BoxButton(
                    text="Quiz",
                    link="#"
                )
            ],
            on_click="#"
        ),
        ItemBox(
            title="Kanji",
            body="0/XX Kanjis Mastered",
            buttons=[
                ItemBox.BoxButton(
                text="Learn",
                link="#"
                ),
                ItemBox.BoxButton(
                    text="Quiz",
                    link="#"
                )
            ],
        ),
    )

    config.register_section(quick_access)

    config.add_separator()

    # Assuming this is inside a method of a User class
    recent = HomeSection("Recently Viewed")

    lang_code = Languages.JAPANESE.obj().code

    # Ensure the user's Japanese stats are created if they don't exist
    if not current_user.get_language_stats(lang_code):
        current_user.create_language_stats(lang_code)

    recent.add_items(
        ItemBox(
            title="Grammar: Te-Form",
            body="The Basics of Japanese Grammar",
            buttons=[
                ItemBox.BoxButton(
                    text="View",
                    link=url_for('nihongo.grammar', slug='te-form')
                )
            ],
            on_click=url_for('nihongo.grammar', slug='te-form')
        ),
        ItemBox(
            title="Kanji: Lesson 3",
            body="Mastering the First 20 Kanji",
            buttons=[
                ItemBox.BoxButton(
                    text="View",
                    link="#"
                )
            ],
            on_click="#"
        )
    )

    config.register_section(recent)

    return render_template('home.html', config=config)

@nihongo_bp.route('/grammar/')
@nihongo_bp.route('/grammar/<slug>')
@login_required
def grammar(slug=None):
    # Validate slug to prevent directory traversal attacks
    if slug and VALID_SLUG.match(slug):
        try:
            lesson_data = get_processor().load(slug)
        except FileNotFoundError:
            flash("Lesson not found.", "error")
            return redirect(url_for('nihongo.grammar'))
        except Exception as e:
            current_app.logger.error(f"An error occurred while loading the lesson {slug}: {str(e)}")
            flash(f"An error occurred while loading the lesson.", "error")
            return redirect(url_for('nihongo.grammar'))

        return render_template(
            'lesson.html',
            lesson=lesson_data,
            data_root=lesson_data.get("data_root")
        )

    lessons = get_processor().get_lessons() # Get all grammar lessons and categories
    return render_template('grammar.html', lessons=lessons)


@nihongo_bp.route('/grammar/api/quiz/<lesson_slug>', methods=['GET'])
def get_quizzes(lesson_slug):
    # Validate slug to prevent directory traversal attacks
    if not lesson_slug or not VALID_SLUG.match(lesson_slug):
        abort(400, description="Invalid lesson slug.")

    base_dir = os.path.join(get_processor().data_root, 'quizzes')
    path = os.path.join(base_dir, f"{lesson_slug}.json")

    # Ensure the resolved path is still inside the quizzes directory
    if not os.path.realpath(path).startswith(os.path.realpath(base_dir)):
        abort(400, description="Invalid path.")

    if not os.path.exists(path):
        return jsonify({"error": "Quiz not found."}), 404

    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f) # Validates JSON by attempting to load it

            processor = get_processor()

            def transform_quiz_text(data, processor):
                if isinstance(data, dict):
                    return {k: transform_quiz_text(v, processor) for k, v in data.items()} # Recursive transformation of all strings
                elif isinstance(data, list):
                    return [transform_quiz_text(item, processor) for item in data] 
                elif isinstance(data, str):
                    return processor.apply_transforms(data)
                else:
                    return data

            data = transform_quiz_text(data, processor)
    except Exception:
        return jsonify({"error": "Malformed quiz JSON."}), 500

    return jsonify(data)
    