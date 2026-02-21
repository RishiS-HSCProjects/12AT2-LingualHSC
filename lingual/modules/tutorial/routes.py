import os
import re
from flask import Blueprint, abort, current_app, flash, jsonify, redirect, render_template, request, url_for, make_response
from lingual.modules.tutorial.utils import quiz_utils
from lingual.modules.tutorial.utils.lessons_processor import get_processor
from lingual.utils.languages import Languages

tutorial_bp = Blueprint(
    Languages.TUTORIAL.obj().app_code,
    __name__,
    url_prefix='/tutorial',
    template_folder='templates',
    static_folder='static',
    static_url_path='/modules/tutorial/static'
)

VALID_SLUG = re.compile(r'^[a-zA-Z0-9\-]+$')

@tutorial_bp.route('/')
def home():
    from lingual.utils.home_config import HomeConfig, HomeSection, HomeBanner, ItemBox

    config = HomeConfig()

    welcome_banner = HomeBanner("Welcome to the tutorial module!")
    config.register_section(welcome_banner)

    quick_access = HomeSection("Quick Access")
    quick_access.add_items(
        ItemBox(
            title="Lessons",
            body="Want to know how our lessons work?",
            buttons=[
                ItemBox.BoxButton(
                text="Click here!",
                link=url_for('tutorial.lessons')
                )
            ],
            on_click=url_for('tutorial.lessons')
        ),
        ItemBox(
            title="Create an account",
            body="Like what you see? Create an account to start learning!",
            buttons=[
                ItemBox.BoxButton(
                text="Sign Up",
                link=url_for('main.register')
                )
            ],
            on_click=url_for('main.register')
        ),
        ItemBox(
            title="Return to Lingual Home",
            body="Want to return to the main home page?",
            buttons=[
                ItemBox.BoxButton(
                text="Take me back!",
                link=url_for('main.landing')
                )
            ],
            on_click=url_for('main.landing')
        )
    )

    config.register_section(quick_access)

    dev = HomeSection("For Developers")
    dev.add_items(
        ItemBox(
            title="Create your own lessons!",
            body="Want to contribute to this open-source project? Start here!",
            buttons=[
                ItemBox.BoxButton(
                text="Learn More",
                link=url_for('tutorial.lessons', slug="for-developers")
                ),
                ItemBox.BoxButton(
                text="Fork Repo",
                link="https://github.com/RishiS-HSCProjects/12AT2-LingualHSC/fork"
                )
            ],
            on_click=url_for('tutorial.lessons', slug="for-developers")
        ),
        ItemBox(
            title="Explore the codebase",
            body="Interested in how this Lingual HSC works? Check out the project on GitHub!",
            buttons=[
                ItemBox.BoxButton(
                text="Open GitHub Repo",
                link="https://github.com/RishiS-HSCProjects/12AT2-LingualHSC"
                )
            ],
            on_click="https://github.com/RishiS-HSCProjects/12AT2-LingualHSC"
        )
    )

    config.register_section(dev)

    return render_template('tutorial-home.html', config=config)

@tutorial_bp.route('/lessons/')
@tutorial_bp.route('/lessons/<slug>')
def lessons(slug=None):
    if slug and VALID_SLUG.match(slug):
        try:
            lesson_data = get_processor().load(slug)
        except FileNotFoundError:
            flash("Lesson not found.", "error")
            return redirect(url_for('tutorial.lessons'))
        except Exception as e:
            current_app.logger.error(f"An error occurred while loading the lesson {slug}: {str(e)}")
            flash(f"An error occurred while loading the lesson.", "error")
            return redirect(url_for('tutorial.lessons'))

        return render_template(
            'tutorial-lesson.html',
            lesson=lesson_data,
            data_root=lesson_data.get("data_root")
        )

    lessons = get_processor().get_lessons()
    return render_template('tutorial-lesson-directory.html', lessons=lessons)


@tutorial_bp.route('/lessons/api/quiz/<lesson_slug>', methods=['GET'], strict_slashes=False)
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

@tutorial_bp.route('/lessons/api/audio', methods=['GET', 'OPTIONS'], strict_slashes=False)
@tutorial_bp.route('/lessons/api/audio/', methods=['GET', 'OPTIONS'], strict_slashes=False)
def get_audio():
    # Handle CORS preflight requests
    if request.method == 'OPTIONS':
        response = make_response('', 204)
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response
    
    audio_id = request.args.get('id')
    if not audio_id:
        abort(400, description="Missing audio ID.")

    # Normalize Windows-style paths to URL-safe paths
    audio_id = audio_id.replace("\\", "/")

    response = make_response(jsonify({
        "path": url_for('tutorial.static', filename=f'audio/{audio_id}')
    }))
    # Add CORS header to allow cross-origin requests
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response
