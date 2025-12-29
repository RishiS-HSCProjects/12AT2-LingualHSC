from flask import url_for, redirect
from flask.blueprints import Blueprint

main_bp = Blueprint(
    'main',
    __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/modules/main/static'
)

@main_bp.route('/')
def landing():
    return "Welcome to the Lingual HSC Module!"

@main_bp.route('/login')
def login():
    return "This is the login page for Lingual HSC."

@main_bp.route('/register')
def register():
    return "This is the registration page for Lingual HSC."
