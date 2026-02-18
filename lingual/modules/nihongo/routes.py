import os
import re
import uuid
from flask import Blueprint, abort, current_app, flash, jsonify, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required
from lingual import db
from lingual.modules.nihongo.utils.kanji_processor import Kanji
from lingual.modules.nihongo.utils import quiz_utils
from lingual.modules.nihongo.utils.grammar_lesson_processor import get_processor
from lingual.utils.languages import Languages
from lingual.utils.lesson_processor import LessonFetchException

nihongo_bp = Blueprint(
    Languages.JAPANESE.obj().app_code,
    __name__,
    url_prefix='/nihongo',
    template_folder='templates',
    static_folder='static',
    static_url_path='/modules/nihongo/static'
)

VALID_SLUG = re.compile(r'^[a-zA-Z0-9\-]+$')

# Server-side quiz cache: {quiz_id: {type, title, data}}
# Initially, quizzes were stored in the session, but that
# resulted in the session cookie becoming too large due to
# the size of the quiz data. While it was not a fatal error,
# caching data in a private variable on the server-side is
# a better, risk-free approach.
# Documented on 16 Feb 2026
_quiz_cache = {}

@nihongo_bp.route('/')
@login_required
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

    # However, the home config should be dynamic to some
    # extent, since it includes user-specific data like
    # recent lessons and the welcome message. After
    # testing, it seems that the overhead of building the
    # home config is not as significant as projected
    # earlier on, so I will not implement a caching
    # mechanism for the home config for now. Ideally, such
    # configs should be built once on startup and stored
    # similar to a Jinja2 template that can be rendered with
    # data dynamically. However, due to time constraints, I
    # will not be building this system for this project, but
    # it is something I would like to implement in the future.
    # Documented on 18 Feb 2026 
    from lingual.utils.home_config import HomeConfig, HomeSection, HomeBanner, ItemBox
    from lingual.utils.languages import get_translatable
    from lingual.modules.nihongo.utils.grammar_lesson_processor import get_processor
    from lingual.modules.nihongo.utils.kanji_processor import Kanji

    lang_code = Languages.JAPANESE.obj().code
    # Ensure the user's Japanese stats are created if they don't exist
    if not current_user.get_language_stats(lang_code):
        current_user.create_language_stats(lang_code)
        db.session.commit()

    config = HomeConfig()

    welcome_banner = HomeBanner(get_translatable('jp', 'home_welcome_text').replace("{first_name}", current_user.first_name))
    config.register_section(welcome_banner)

    lessons_practised = (stats := current_user.get_language_stats(lang_code)) and stats.get_lessons_practised() or []

    quick_access = HomeSection("Quick Access")
    quick_access.add_items(
        ItemBox(
            title="Grammar",
            body=f"{len(lessons_practised)}/{sum(
                len(category['lessons']) for category in get_processor().get_lessons()
            )} Grammar Lessons Completed",
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
            body=f"0/{len(Kanji.get_prescribed_kanji())} Kanji Mastered",
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

    recent_lessons = lessons_practised[-3:][::-1] if lessons_practised else None

    if recent_lessons:
        for lesson in recent_lessons:
            lesson = get_processor().get_lesson(lesson)
            recent.add_items(
                ItemBox(
                    title=lesson.title,
                    body=lesson.summary,
                    buttons=[
                        ItemBox.BoxButton(
                            text="View",
                            link=url_for('nihongo.grammar', slug=lesson.slug)
                        )
                    ],
                    on_click=url_for('nihongo.grammar', slug=lesson.slug)
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

                    quiz_id = str(uuid.uuid4()) # Unique identifier for the quiz session
                    quiz_data['id'] = quiz_id 
                    # Cache quiz by its unique ID
                    _quiz_cache[quiz_id] = {
                        "type": quiz_type.name,
                        "title": quiz_data.get('title', 'Quiz'),
                        "data": quiz_data
                    }
                    # Store only the quiz ID in session for retrieval
                    session['active_quiz_id'] = quiz_id

                    # Go to quiz session page
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
    quiz_id = session.get('active_quiz_id')
    if not quiz_id or quiz_id not in _quiz_cache:
        flash("No active quiz found. Please try again.", "warning")
        return redirect(url_for('nihongo.quiz')) # Redirect to quiz generation page if no active quiz is found

    payload = _quiz_cache[quiz_id] # Retrieve quiz data

    return render_template(
        'quiz-session.html',
        quiz_payload=payload['data'],
        quiz_title=payload.get('title', 'Quiz')
    )

@nihongo_bp.route('/grammar/api/quiz-complete', methods=['POST'])
@login_required
def lesson_quiz_complete():
    payload = request.get_json(silent=True) or {}
    lesson_slug = payload.get("lesson")
    if not lesson_slug:
        abort(400, description="Missing lesson slug.")

    # Update user's progress for the lesson
    stats = current_user.get_language_stats(Languages.JAPANESE.obj().code)
    stats.add_lesson_practised(lesson_slug)
    db.session.commit()

    return jsonify({"status": "success"})
