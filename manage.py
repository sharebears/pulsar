#!/usr/bin/env python3

from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from pulsar import create_app, db

app = create_app('config.py')
manager = Manager(app)
migrate = Migrate(app, db)  # noqa
manager.add_command('db', MigrateCommand)


if __name__ == '__main__':
    manager.run()
