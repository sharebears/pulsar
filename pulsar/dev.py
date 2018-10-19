#!/usr/bin/env python3
from collections import defaultdict

import click
import flask
import sqlalchemy
from flask.cli import with_appcontext

from core import cache, db
from core.test_data import CorePopulator
from core.users.models import User
from forums.test_data import ForumsPopulator
from messages.test_data import MessagesPopulator
from core.users.permissions import SitePermissions

app = flask.current_app

POPULATORS = [
    CorePopulator,
    ForumsPopulator,
    MessagesPopulator,
    ]


@click.group()
def dev():
    """Perform development related tasks."""
    pass


@dev.command()
@with_appcontext
def createdb():
    """Create an empty database per the current schema."""
    db.create_all()


@dev.command()
@with_appcontext
def createdata():
    """Recreate and repopulate an existing testing database."""
    with app.test_request_context():
        flask.g.cache_keys = defaultdict(set)
        try:
            user = User.from_pk(1)
        except sqlalchemy.exc.ProgrammingError as e:
            click.secho(
                'Please manually create the database before running the createdata command.',
                fg='red', bold=True)
            raise click.Abort
        if user and user.username != 'user_one':
            click.secho('The username of the first user is not user_one. Are you sure this '
                        'is a testing database? Please clear it yourself and re-try.',
                        fg='red', bold=True)
            raise click.Abort
        cache.clear()
        db.session.commit()
    with app.app_context():
        db.drop_all()
        db.create_all()
    with app.test_request_context():
        for p in POPULATORS:
            p.populate()
        CorePopulator.add_permissions(SitePermissions.GOD_MODE)
        cache.clear()
    click.secho(f'Updated and inserted development data into the database!')
