import flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy, event
from werkzeug import find_modules, import_string

from pulsar.base_model import BaseModel
from pulsar.cache import Cache, clear_cache_dirty
from pulsar.serializer import NewJSONEncoder
from pulsar.exceptions import (  # noqa
    APIException, _500Exception, _405Exception, _404Exception,
    _403Exception, _401Exception, _312Exception)

db = SQLAlchemy(model_class=BaseModel)
cache = Cache()
migrate = Migrate()

event.listen(db.session, 'before_flush', clear_cache_dirty)


def create_app(config: str) -> 'flask.Flask':
    app = flask.Flask(__name__, instance_relative_config=True)
    app.config.from_pyfile(config)
    app.json_encoder = NewJSONEncoder

    global cache
    db.init_app(app)
    cache.init_app(app)
    migrate.init_app(app, db)

    with app.app_context():
        register_blueprints(app)
        register_error_handlers(app)

    return app


def register_blueprints(app: 'flask.Flask') -> None:
    # Every sub-view needs to be imported to populate the blueprint.
    # If this is not done, we will have empty blueprints.
    # If we register every module with the ``bp`` attribute normally,
    # we would have a lot of duplicate routes, which Werkzeug doesn't filter.
    for name in find_modules('pulsar', recursive=True):
        import_string(name)

    # Now import and register each blueprint. Since each blueprint
    # is defined in the package's __init__, we scan packages this time,
    # unlike the last.
    for name in find_modules('pulsar', include_packages=True):
        mod = import_string(name)
        if hasattr(mod, 'bp'):
            app.register_blueprint(mod.bp)

    # print(app.url_map)  # debug


def register_error_handlers(app: 'flask.Flask') -> None:
    app.register_error_handler(APIException, lambda err: (
        flask.jsonify(err.message), err.status_code))
    app.register_error_handler(404, _404_handler)
    app.register_error_handler(405, _405_handler)
    app.register_error_handler(500, _500_handler)


def _404_handler(_) -> flask.Response:
    return flask.jsonify(_404Exception().message), 404


def _405_handler(_) -> flask.Response:
    return flask.jsonify(_405Exception().message), 405


def _500_handler(_) -> flask.Response:
    return flask.jsonify(_500Exception().message), 500
