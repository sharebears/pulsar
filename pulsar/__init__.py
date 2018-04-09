from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from werkzeug import find_modules, import_string
from pulsar.exceptions import (  # noqa
    APIException, _500Exception, _405Exception, _404Exception,
    _403Exception, _401Exception, _312Exception)

db = SQLAlchemy()
ma = Marshmallow()


def create_app(config):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_pyfile(config)

    db.init_app(app)
    ma.init_app(app)

    with app.app_context():
        register_blueprints(app)
        register_error_handlers(app)

    return app


def register_blueprints(app):
    for name in find_modules('pulsar', recursive=True):
        mod = import_string(name)
        if hasattr(mod, 'bp'):
            app.register_blueprint(mod.bp)


def register_error_handlers(app):
    app.register_error_handler(APIException, lambda err: (
        jsonify(err.message), err.status_code))
    app.register_error_handler(404, _404_handler)
    app.register_error_handler(405, _405_handler)
    app.register_error_handler(500, _500_handler)


def _404_handler(_):
    return jsonify(_404Exception().message), 404


def _405_handler(_):
    return jsonify(_405Exception().message), 405


def _500_handler(_):
    return jsonify(_500Exception().message), 500
