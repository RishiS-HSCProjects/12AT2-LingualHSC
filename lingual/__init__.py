from flask import Flask

def create_app():

    app = Flask(__name__)

    # Register all blueprints
    from lingual.modules.nihongo.routes import nihongo_bp
    from lingual.main.routes import main_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(nihongo_bp)

    return app
