#!/usr/bin/env python3

import flask
from flask_cors import CORS
from flask_migrate import Migrate

import core
import forums
import rules
from core import db

migrate = Migrate()


def create_app(config: str) -> flask.Flask:
    app = flask.Flask(__name__, instance_relative_config=True)
    app.config.from_pyfile(config)

    migrate.init_app(app, db)
    CORS(app)

    core.init_app(app)
    forums.init_app(app)
    rules.init_app(app)

    return app


app = create_app('config.py')

if __name__ == '__main__':
    app.run()
