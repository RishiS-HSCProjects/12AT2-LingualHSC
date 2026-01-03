import os
from flask import Flask
from dotenv import load_dotenv


class Config:
    """ Configuration settings for Lingual HSC Flask application. """
    load_dotenv()  # Load environment variables from .env file

    SECRET_KEY = os.getenv('SECRET_KEY')

def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static') # Create app instance
    app.config.from_object(Config) # Attach config

    # Register all blueprints
    from lingual.core.auth.routes import auth_bp
    from lingual.main.routes import main_bp
    from lingual.modules.nihongo.routes import nihongo_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(nihongo_bp)

    return app
