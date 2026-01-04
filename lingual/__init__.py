import os
from flask import Flask
from dotenv import load_dotenv
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

mail = Mail()  # Initialize main module
db = SQLAlchemy()  # Placeholder for database instance
login_manager = LoginManager() # Placeholder for login manager
login_manager.login_view = 'main.login'  # Set login view
login_manager.login_message_category = 'warning'  # Set login message category
migrate = Migrate()  # Placeholder for database migration

class Config:
    """ Configuration settings for Lingual HSC Flask application. """
    load_dotenv()  # Load environment variables from .env file

    SECRET_KEY          =      os.getenv('SECRET_KEY')
    MAIL_SERVER         =      os.getenv('MAIL_SERVER')
    MAIL_PORT           =      os.getenv('MAIL_PORT')
    MAIL_USE_TLS        =      os.getenv('MAIL_USE_TLS')
    MAIL_USE_SSL        =      os.getenv('MAIL_USE_SSL')
    MAIL_USERNAME       =      os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD       =      os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER =      os.getenv('MAIL_DEFAULT_SENDER')

    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(os.path.abspath(os.path.dirname(__file__)), 'core', 'data', 'lingual.db')}"


def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static') # Create app instance
    app.config.from_object(Config) # Attach config

    mail.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    # Register all blueprints
    from lingual.core.auth.routes import auth_bp
    from lingual.main.routes import main_bp
    from lingual.modules.nihongo.routes import nihongo_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(nihongo_bp)

    return app
