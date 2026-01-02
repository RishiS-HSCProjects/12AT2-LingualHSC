import os
from flask import Flask
from dotenv import load_dotenv


class Config:
    """ Configuration settings for Lingual HSC Flask application. """
    SECRET_KEY = os.getenv('SECRET_KEY')

    if SECRET_KEY is None:
        raise RuntimeError("SECRET_KEY environment variable not set.")

def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static') # Create app instance
    app.config.from_object(Config) # Attach config

    load_dotenv()  # Load environment variables from .env file

    # Register all blueprints
    from lingual.modules.nihongo.routes import nihongo_bp
    from lingual.main.routes import main_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(nihongo_bp)

    return app
