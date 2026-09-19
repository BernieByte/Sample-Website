from pathlib import Path

from flask import Flask

from .config import Config
from .db import init_db
from .routes.auth import auth_bp
from .routes.files import files_bp
from .routes.views import views_bp

BASE_DIR = Path(__file__).resolve().parent.parent


def create_app():
    app = Flask(
        __name__,
        template_folder=str(BASE_DIR / "templates"),
        static_folder=str(BASE_DIR / "static"),
    )
    app.config.from_object(Config)

    init_db(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(files_bp)
    app.register_blueprint(views_bp)

    return app
