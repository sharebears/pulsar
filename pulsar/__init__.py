import flask
from flask_cors import CORS
from flask_migrate import Migrate

import core
import forums
from core import db

migrate = Migrate()


def create_app(config: str) -> flask.Flask:
    app = flask.Flask(__name__, instance_relative_config=True)
    CORS(app)
    app.config.from_pyfile(config)

    core.init_app(app)
    forums.init_app(app)
    migrate.init_app(app, db)

    return app
