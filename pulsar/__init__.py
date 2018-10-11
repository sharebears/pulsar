import flask
import core
import forums
from flask_cors import CORS
from flask_migrate import Migrate

migrate = Migrate()


def create_app(config: str) -> flask.Flask:
    app = flask.Flask(__name__, instance_relative_config=True)
    CORS(app)
    app.config.from_pyfile(config)

    db = core.init_app(app)
    forums.init_app(app)
    migrate.init_app(app, db)

    return app
