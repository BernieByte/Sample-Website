from pathlib import Path

from flask import Flask

from .config import Config
from .db import init_db
from .routes.auth import auth_bp
from .routes.files import files_bp
from .routes.views import views_bp


def create_app():
    project_root = Path(__file__).resolve().parent.parent
    app = Flask(
        __name__,
        template_folder=str(project_root),
        static_folder=str(project_root / "static"),
    )
    app.config.from_object(Config)

    init_db(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(files_bp)
    app.register_blueprint(views_bp)

    return app
