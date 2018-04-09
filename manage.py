#!/usr/bin/env python3

import sys
import subprocess
from flask_script import Manager, Command
from flask_migrate import Migrate, MigrateCommand
from pulsar import create_app, db

app = create_app('config.py')
manager = Manager(app)


if len(sys.argv) > 1 and sys.argv[1] == 'db':
    db.init_app(app)
    migrate = Migrate(app, db)  # noqa
manager.add_command('db', MigrateCommand)


@manager.add_command
class Document(Command):
    """Autogenerate code .rst files."""
    name = 'docs'

    def run(self):
        subprocess.call(['sphinx-apidoc', '-M', '-o', 'docs/source', 'pulsar'])


if __name__ == '__main__':
    manager.run()
