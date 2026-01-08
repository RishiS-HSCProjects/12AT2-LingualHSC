from flask import Blueprint, redirect, url_for
from flask_login import login_required
from lingual.utils.languages import Languages

nihongo_bp = Blueprint(
    Languages.JAPANESE.obj().app_name,
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

@nihongo_bp.route('/grammar')
def grammar():
    return "Nihongo Grammar"
