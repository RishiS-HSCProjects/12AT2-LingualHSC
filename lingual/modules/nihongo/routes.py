import os
import re
from flask import Blueprint, abort, flash, json, jsonify, redirect, render_template, url_for
from flask_login import login_required
from lingual.utils.languages import Languages
from lingual.modules.nihongo.utils.lesson_processor import get_processor

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
    return "Welcome to the Nihongo Module!"

@nihongo_bp.route('/grammar/', defaults={'slug': None})
@nihongo_bp.route('/grammar/<slug>')
@login_required
def grammar(slug):
    # Validate slug to prevent directory traversal attacks
    if not VALID_SLUG.match(slug):
        abort(400, description="Invalid lesson slug.")

    try:
        lesson_data = get_processor().load(slug)
    except FileNotFoundError:
        flash("Lesson not found.", "error")
        return redirect(url_for('nihongo.grammar'))
    except Exception as e:
        flash(f"An error occurred while loading the lesson: {str(e)}", "error")
        return redirect(url_for('nihongo.grammar'))

    return render_template('lesson.html', lesson=lesson_data, data_root=lesson_data.get("data_root"))

@nihongo_bp.route('grammar/api/quiz/<lesson_slug>', methods=['GET'])
def get_quizzes(lesson_slug):
    # Validate slug to prevent directory traversal attacks
    if not VALID_SLUG.match(lesson_slug):
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
    