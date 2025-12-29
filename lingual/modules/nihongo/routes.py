from flask import Blueprint

nihongo_bp = Blueprint(
    'nihongo',
    __name__,
    url_prefix='/nihongo',
    template_folder='templates',
    static_folder='static',
    static_url_path='/modules/nihongo/static'
)

@nihongo_bp.route('/')
def home():
    return "Welcome to the Nihongo Module!"

@nihongo_bp.route('/grammar')
def grammar():
    return "Nihongo Grammar"
