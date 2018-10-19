#!/usr/bin/env python3
from collections import defaultdict

import click
import flask
from flask.cli import with_appcontext

from core import cache, db
from core.test_data import CorePopulator

app = flask.current_app

POPULATORS = [
    CorePopulator,
    ]


@click.group()
def dev():
    """Perform development related tasks."""
    pass


@dev.command()
@with_appcontext
def createdata():
    with app.test_request_context():
        flask.g.cache_keys = defaultdict(set)
        db.drop_all()
        db.create_all()
        for p in POPULATORS:
            p.populate()
        cache.clear()
