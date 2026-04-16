import os
import re
from flask import Blueprint, abort, current_app, flash, jsonify, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required
from lingual import db
from lingual.modules.nihongo.utils.kanji_processor import Kanji
from lingual.modules.nihongo.utils import quiz_utils
from lingual.modules.nihongo.utils.grammar_lesson_processor import get_processor
from lingual.modules.nihongo.utils.particle_tiles_processor import ParticleTilesProcessor
from lingual.utils.form_manager import flash_all_form_errors
from lingual.utils.languages import Languages
from lingual.utils.tiles_utils import TileSection

# Blueprint for the Nihongo module, handling routes related to Japanese language learning, including grammar lessons, kanji reference, and quizzes.
nihongo_bp = Blueprint(
    Languages.JAPANESE.obj().app_code,
    __name__,
    url_prefix='/nihongo',
    template_folder='templates',
    static_folder='static',
    static_url_path='/modules/nihongo/static'
)

# Regular expression to validate lesson slugs, allowing only alphanumeric characters and hyphens to prevent directory traversal and ensure valid slugs.
VALID_SLUG = re.compile(r'^[a-zA-Z0-9\-]+$')

# T-FE03 --> Server-side quiz cache: {quiz_id: {type, title, data}}
_quiz_cache = {}

_particles_processor = ParticleTilesProcessor()

@nihongo_bp.route('/')
@login_required
def home():
    # D-AE05
    from lingual.utils.home_config import HomeConfig, HomeSection, HomeBanner, ItemBox, ItemParagraph
    from lingual.utils.languages import get_translatable
    from lingual.modules.nihongo.utils.grammar_lesson_processor import get_processor

    lang_code = Languages.JAPANESE.obj().code
    # Ensure the user's Japanese stats are created if they don't exist
    if not current_user.get_language_stats(lang_code):
        current_user.create_language_stats(lang_code)
        db.session.commit() # Commit the new stats to the database

    config = HomeConfig()

    # Personalised welcome banner with user's first name
    welcome_banner = HomeBanner(get_translatable('jp', 'home_welcome_text').replace("{first_name}", current_user.first_name))

    # Get the list of grammar lessons practised by the user to display progress and recent lessons on the home page
    grammar_practised = (stats := current_user.get_language_stats(lang_code)) and stats.get_grammar_practised() or []

    # Quick access section with links to grammar and kanji sections, showing progress for grammar lessons
    quick_access = HomeSection("Quick Access")
    quick_access.add_items(
        ItemBox(
            title="Grammar",
            body=f"{len(grammar_practised)}/{sum( # Total number of grammar lessons learned out of total available lessons
                len(category['lessons']) for category in get_processor().get_lessons()
            )} Grammar Lessons Completed",
            buttons=[
                ItemBox.BoxButton(
                text="Learn",
                link=url_for('nihongo.grammar')
                ),
                ItemBox.BoxButton(
                    text="Quiz",
                    link = url_for('nihongo.quiz', type=quiz_utils.NihongoQuizTypes.GRAMMAR.name) # Quick access to grammar quiz
                )
            ],
            on_click=url_for('nihongo.grammar') # Make the whole box clickable to go to the grammar section
        ),
        ItemBox(
            title="Kanji",
            body=f"Your quick kanji reference sheet!",
            buttons=[
                ItemBox.BoxButton(
                text="Learn",
                link=url_for('nihongo.kanji') # Quick access to kanji reference section
                )
            ],
            on_click=url_for('nihongo.kanji') # Make the whole box clickable to go to the kanji section
        )
    )

    indev = HomeSection("Indev")
    indev.add_items(
        ItemParagraph(
            "These items are currently under development. If you encounter any issues, please make an issue on our GitHub Page!"
        ),
        ItemBox(
            title="Particles",
            body="Particle Cheat Sheet!",
            buttons=[
                ItemBox.BoxButton(
                text="Open Demo",
                link=url_for('nihongo.particles')
                )
            ]
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
                    link="#" # Placeholder link for vocab quiz, to be implemented in the future
                )
            ],
            # Provide a disabled reason and flash category to indicate that this feature is not yet available
            disabled_reason="Vocab section coming soon!",
            disabled_flash_category="info"
        )
    )

    recent = HomeSection("Recently Viewed")
    recent_lessons = grammar_practised[-3:][::-1] if grammar_practised else None # Get the 3 most recently practised grammar lessons, reversed to show most recent first
    if recent_lessons: # Ensure there are practised lessons to show before attempting to display them
        for lesson in recent_lessons: # Iterate through lessons to display them in the recent section
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
                    on_click=url_for('nihongo.grammar', slug=lesson.slug) # Make the whole box clickable to go to the lesson page
                )
            )

    # Register the sections in the desired order
    config.register_section(welcome_banner)
    config.register_section(quick_access)
    config.add_separator()
    config.register_section(recent)
    config.register_section(indev)

    return render_template('nihongo-home.html', config=config)

@nihongo_bp.route('/grammar/')
@nihongo_bp.route('/grammar/<slug>')
@login_required
def grammar(slug=None):
    # Validate slug to prevent directory traversal attacks
    if slug and VALID_SLUG.match(slug):
        try:
            # Attempt to load the lesson data using the processor, applying transformations
            lesson_data = get_processor().load(slug)
        except FileNotFoundError: # If the lesson file is not found, flash an error message and redirect to the directory
            flash("Lesson not found.", "error")
            return redirect(url_for('nihongo.grammar')) # Go to lesson directory
        except Exception as e:
            # Log any unexpected errors that occur during lesson loading and flash a generic error message to the user
            current_app.logger.error(f"An error occurred while loading the lesson {slug}: {str(e)}")
            flash(f"An error occurred while loading the lesson.", "error")
            return redirect(url_for('nihongo.grammar'))
        
        # Get source URL for edit hyperlink
        from lingual.modules.nihongo import GIT_GRAMMAR_DIRECTORY
        lesson_data['source_url'] = f"{GIT_GRAMMAR_DIRECTORY}/lessons/{slug}.md"

        return render_template(
            # Render lesson page
            'nihongo-lesson.html',
            lesson=lesson_data,
            data_root=lesson_data.get("data_root")
        )

    lessons = get_processor().get_lessons() # Get all grammar lessons and categories
    return render_template('nihongo-grammar.html', lessons=lessons) # Render the grammar directory with the list of lessons and categories


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
        data = quiz_utils.load_quiz_data(lesson_slug) # Load quiz data for the specified lesson slug, applying any necessary transformations using the lesson processor
    except Exception:
        return jsonify({"error": "Malformed quiz JSON."}), 500

    if not data:
        return jsonify({"error": "Quiz not found."}), 404

    return jsonify(data) # Return the quiz data as JSON

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
    
@nihongo_bp.route('/kanji/')
@login_required
def kanji():
    section = TileSection(
        id='kanji',
        title='Prescribed Kanji',
        description='Tap a character to reveal readings and meanings.'
    ).add_tiles(Kanji.get_prescribed_kanji())

    return render_template('nihongo-kanji.html', tile_section=section.to_dict())

@nihongo_bp.route('/kanji/api/<kanji_char>', methods=['GET'])
@login_required
def kanji_lookup(kanji_char):
    """Retrieves kanji data for a specific kanji character.
    If not cached, performs a synchronous fetch from the WaniKani API.
    """

    if not kanji_char or kanji_char.isspace():
        # Abort if char missing or just whitespace
        abort(400, description="Invalid kanji.")

    try:
        # Try getting kanji data, which will fetch from WaniKani if not cached
        kanji = Kanji.get_kanji(kanji_char)
    except KeyError:
        current_app.logger.error("WaniKani API key not configured.")
        abort(503, description="WaniKani API key not configured.")
    except Exception as e:
        # Log any unexpected errors that occur during kanji lookup and abort with a generic error message
        current_app.logger.error(f"Failed to fetch kanji data for {kanji_char}: {str(e)}")
        abort(400, description=f"Failed to fetch kanji data: {str(e)}")

    return jsonify({"status": "ready", "data": kanji.data}) # Return the kanji data as JSON

@nihongo_bp.route('/kanji/api/batch', methods=['POST'])
@login_required
def kanji_batch():
    # Get payload containing list of kanji characters to look up
    payload = request.get_json(silent=True) or {}
    items = payload.get("kanji", [])

    if not isinstance(items, list):
        # Abort if incorrect payload structure
        abort(400, description="Invalid payload.")

    # Build a data map of kanji character to kanji data for each character in the list, fetching from WaniKani if not cached
    data_map = {}
    for kanji_char in items:
        try:
            kanji = Kanji.get_kanji(kanji_char)
        except Exception as e:
            # Log any unexpected errors that occur during kanji lookup and skip the character, allowing the batch process to continue for other characters
            current_app.logger.error(f"Failed to fetch kanji data for {kanji_char}: {str(e)}")
            continue
        data_map[kanji_char] = kanji.data # Append kanji data to the data map

    return jsonify({"status": "ready", "data": data_map}) # Return the batch kanji data as JSON

@nihongo_bp.route('/particles/')
@login_required
def particles():
    section = _particles_processor.build_tile_section() # Build section
    return render_template('nihongo-particles.html', tile_section=section.to_dict())

@nihongo_bp.route('/particles/api/<slug>', methods=['GET'])
@login_required
def particles_lookup(slug):
    if not slug or not VALID_SLUG.match(slug):
        abort(400, description="Invalid particle slug.")

    try:
        # Attempt to load particle data using the processor, which will handle caching and fetching as needed
        payload = _particles_processor.load_particle(slug)
    except FileNotFoundError:
        abort(404, description="Particle note not found.")
    except ValueError:
        abort(400, description="Invalid particle slug.")
    except Exception as e:
        current_app.logger.error(f"Failed to load particle note for {slug}: {str(e)}")
        abort(500, description="An error occurred while loading particle notes.")

    return jsonify({"status": "ready", "data": payload})

@nihongo_bp.route('/quiz', methods=['GET', 'POST'])
@login_required
def quiz():
    """ Route for Lingual Quizzes """

    # Get quiz types and their associated modals
    quiz_topics = quiz_utils.NihongoQuizTypes
    quiz_modals = {}

    # Build quiz modal instances once so validation state is preserved on re-render.
    for topic in quiz_topics:
        try:
            modal = topic.get_modal() # Attempt to get the quiz modal
            if modal:
                # Store modal instance if exists
                quiz_modals[topic] = modal
        except NotImplementedError:
            continue # If modal not implemented, just skip it

    quiz_type_query = request.args.get('type') or None # Requested quiz type

    # quiz_type: QuizTypes value of the quiz type to be rendered, if valid and requested.
    # None if no valid type requested or on initial GET request without query parameters.
    quiz_type = None

    if quiz_type_query:
        # Auto-opens quiz modal if a valid quiz type is provided in the query parameters
        try:
            selected_type = quiz_utils.NihongoQuizTypes[quiz_type_query.upper()] # Find enum
            if selected_type in quiz_modals:
                quiz_type = selected_type # Set quiz type if valid and has an associated modal
            else:
                # Not implemented quiz types will be listed but not have modals, flash a notification
                flash(f"{selected_type.name.title()} Quiz not implemented.", "warning")
        except KeyError:
            quiz_type = None # Invalid quiz type in query, ignore and render page without auto-opening a modal

    quiz_form = quiz_modals.get(quiz_type) if quiz_type else None # Get the quiz form associated with the requested quiz type, if any

    if request.method == 'POST' and quiz_type and quiz_form:
        # Handle quiz configuration form submission, validating the form and generating the quiz if valid, otherwise flashing errors
        if quiz_form.validate_on_submit():
            try:
                if quiz_type == quiz_utils.NihongoQuizTypes.GRAMMAR:
                    # Handle grammar quiz
                    selected_lessons = quiz_form.lessons.data # type: ignore
                    max_questions = quiz_form.max_questions.data # type: ignore
                    quiz_data = quiz_utils.build_grammar_quiz(selected_lessons, max_questions)

                    quiz_data['user_id'] = current_user.id
                    # Cache quiz by user's unique ID
                    _quiz_cache[current_user.id] = {
                        "type": quiz_type.name,
                        "title": quiz_data.get('title', 'Quiz'),
                        "data": quiz_data
                    }

                    # Go to quiz session page
                    return redirect(url_for('nihongo.quiz_session'))
                else:
                    # Reject other type attempts
                    flash("Quiz type not supported yet.", "error")
            except Exception as e:
                # Log any unexpected errors that occur during quiz generation and flash a generic error message to the user
                current_app.logger.error(f"Error generating quiz: {str(e)}")
                flash("An error occurred while generating the quiz. Please try again.", "error")
        else:
            # Form validation failed, flash all form errors to the user
            flash_all_form_errors(quiz_form)

    return render_template(
        'nihongo-quiz.html',
        quiz_topics=quiz_topics,
        quiz_modals=quiz_modals,
        quiz_type=quiz_type,
        auto_open_modal=bool(quiz_form)
    )

@nihongo_bp.route('/quiz/session', methods=['GET'])
@login_required
def quiz_session():
    if current_user.id not in _quiz_cache:
        flash("No active quiz found. Please try again.", "warning")
        return redirect(url_for('nihongo.quiz')) # Redirect to quiz generation page if no active quiz is found

    payload = _quiz_cache[current_user.id] # Retrieve quiz data

    # Renders template for the quiz session, passing the quiz data and title to be used in the frontend quiz interface
    return render_template(
        'nihongo-quiz-session.html',
        quiz_payload=payload['data'],
        quiz_title=payload.get('title', 'Quiz')
    )
