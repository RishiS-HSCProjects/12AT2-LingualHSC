from flask import Blueprint, redirect, url_for
from flask_login import current_user, login_required
from lingual.utils.languages import Languages

nihongo_bp = Blueprint(
    Languages.JAPANESE.obj().app_name,
    __name__,
    url_prefix='/nihongo',
    template_folder='templates',
    static_folder='static',
    static_url_path='/modules/nihongo/static'
)

@login_required
@nihongo_bp.route('/')
def home():
    if not current_user.is_authenticated:
        return redirect(url_for('main.login'))
    
    return "Welcome to the Nihongo Module!"

@nihongo_bp.route('/grammar')
def grammar():
    return "Nihongo Grammar"
