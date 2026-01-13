from flask import Blueprint, flash, redirect, render_template, url_for
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

@nihongo_bp.route('/')
@login_required
def home():
    return "Welcome to the Nihongo Module!"

@nihongo_bp.route('/grammar/<slug>')
@login_required
def grammar(slug):
    if not slug:
        return "Nihongo Grammar Home"
    try:
        lesson_data = get_processor().load(slug)
    except FileNotFoundError as e:
        lesson_data = None
        flash("Lesson not found.", "error")
        return redirect(url_for('nihongo.grammar'))
    except Exception as e:
        flash(f"An error occurred while loading the lesson: {str(e)}", "error")
        return redirect(url_for('nihongo.grammar'))

    return render_template('lesson.html', lesson=lesson_data)
