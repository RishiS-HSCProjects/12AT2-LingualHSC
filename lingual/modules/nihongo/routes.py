from functools import lru_cache
import os
import re
from flask import Blueprint, abort, current_app, flash, jsonify, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required
from lingual import db
from lingual.modules.nihongo.utils.kanji_processor import Kanji
from lingual.utils.languages import Languages
from lingual.modules.nihongo.utils import quiz_utils
from lingual.modules.nihongo.utils.grammar_lesson_processor import get_processor
from lingual.utils.quiz_manager import QuizForm

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
@lru_cache() # Cache the home config to avoid rebuilding it on every request. Since the config is based on static data and user info that doesn't change often, this is a safe optimization.
def home():
    # Since all of my home config setup data exists here,
    # the config gets rebuilt every time the home route
    # is accessed. This unnecessarily adds overhead to
    # the application. I wanted to move this logic to run
    # on compile, but this solution did not work since
    # certain functions like url_for and attributes like
    # and current_user can not be resolved outside of a
    # Flask context, which it is during initialisation.
    # As a result, I will use the lru_cache decorator,
    # similar to the lesson caching.
    # Documented on 12 Feb 2026
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
                    link = url_for('nihongo.quiz', type=quiz_utils.NihongoQuizTypes.GRAMMAR.name)
                )
            ],
            on_click=url_for('nihongo.grammar')
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
                    link = url_for('nihongo.quiz', type=quiz_utils.NihongoQuizTypes.KANJI.name)
                )
            ],
            on_click=url_for('nihongo.kanji')
        ),
        ItemBox(
            title="Vocab",
            body="Practice HSC Prescribed Vocabulary!",
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
            disabled_reason="Vocab section coming soon!",
            disabled_flash_category="info"
        )
    )

    config.register_section(quick_access)

    config.add_separator()

    # Assuming this is inside a method of a User class
    recent = HomeSection("Recently Viewed")

    lang_code = Languages.JAPANESE.obj().code

    # Ensure the user's Japanese stats are created if they don't exist
    if not current_user.get_language_stats(lang_code):
        current_user.create_language_stats(lang_code)
        db.session.commit()

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

    def get_home_config() -> HomeConfig:
        return config


    return render_template('home.html', config=get_home_config())

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

    try:
        data = quiz_utils.load_quiz_data(lesson_slug)
    except Exception:
        return jsonify({"error": "Malformed quiz JSON."}), 500

    if not data:
        return jsonify({"error": "Quiz not found."}), 404

    return jsonify(data)
    
@nihongo_bp.route('/kanji/')
@login_required
def kanji():
    return render_template('kanji.html', prescribed=Kanji.get_prescribed_kanji())

@nihongo_bp.route('/kanji/api/prefetch', methods=['POST'])
@login_required
def kanji_prefetch():
    """ Reserved for client-side prefetch. """
    return jsonify({"status": "ok"})

@nihongo_bp.route('/kanji/api/<kanji_char>', methods=['GET'])
@login_required
def kanji_lookup(kanji_char):
    """Retrieves kanji data for a specific kanji character.
    If not cached, performs a synchronous fetch from the WaniKani API.
    """

    if not kanji_char or kanji_char.isspace():
        abort(400, description="Invalid kanji.")

    try:
        kanji = Kanji.get_kanji(kanji_char)
    except KeyError:
        current_app.logger.error("WaniKani API key not configured.")
        abort(503, description="WaniKani API key not configured.")
    except Exception as e:
        abort(400, description=f"Failed to fetch kanji data: {e}")

    return jsonify({"status": "ready", "data": kanji.data})

@nihongo_bp.route('/kanji/api/batch', methods=['POST'])
@login_required
def kanji_batch():
    payload = request.get_json(silent=True) or {}
    items = payload.get("kanji", [])

    if not isinstance(items, list):
        abort(400, description="Invalid payload.")

    data_map = {}
    for kanji_char in items:
        try:
            kanji = Kanji.get_kanji(kanji_char)
        except Exception:
            continue
        data_map[kanji_char] = kanji.data

    return jsonify({"status": "ready", "data": data_map})

@nihongo_bp.route('/quiz', methods=['GET', 'POST'])
@login_required
def quiz():

    quiz_type = request.args.get('type') or None
    if quiz_type:
        try:
            quiz_type = quiz_utils.NihongoQuizTypes[quiz_type.upper()]
            try:
                quiz_type.get_modal() # Check if modal is implemented. If not, we will not auto open the modal since there is no configuration for the quiz.
            except NotImplementedError:
                flash(f"{quiz_type.name.title()} Quiz not implemented.", "warning")
                quiz_type = None
        except KeyError:
            quiz_type = None

    if request.method == 'POST' and quiz_type:
        form = quiz_type.get_modal() # Get the form associated with the quiz type
        if form.validate_on_submit():
            try:
                if quiz_type == quiz_utils.NihongoQuizTypes.GRAMMAR:
                    selected_lessons = form.lessons.data # type: ignore
                    max_questions = form.max_questions.data # type: ignore
                    quiz_data = quiz_utils.build_grammar_quiz(selected_lessons, max_questions)
                    session['active_quiz'] = {
                        "type": quiz_type.name,
                        "data": quiz_data
                    }
                    return redirect(url_for('nihongo.quiz_session'))
                else:
                    flash("Quiz type not supported yet.", "error")
            except Exception as e:
                current_app.logger.error(f"Error generating quiz: {str(e)}")
                flash("An error occurred while generating the quiz. Please try again.", "error")
        else:
            flash("Invalid input. Please check your selections and try again.", "error")

    return render_template(
        'quiz.html',
        quiz_topics=quiz_utils.NihongoQuizTypes,
        quiz_type=quiz_type,
        auto_open_modal=bool(quiz_type)
    )

@nihongo_bp.route('/quiz/session', methods=['GET'])
@login_required
def quiz_session():
    payload = session.get('active_quiz')
    if not payload or 'data' not in payload:
        flash("No active quiz found. Generate one first.", "warning")
        return redirect(url_for('nihongo.quiz'))

    return render_template(
        'quiz-session.html',
        quiz_payload=payload['data'],
        quiz_title=payload.get('title', 'Quiz')
    )
