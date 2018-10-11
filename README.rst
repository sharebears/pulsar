# pulsar

A BitTorrent Indexer written in python using the Flask micro-framework for the backend,
meant to succeed Gazelle.

## Config
An explanation of configuration options is available in ``config.py.example``. All
configurations should be placed in ``instance/``. A secret key for the application can be 
generated with ``os.urandom``. 

Configuration files are located in ``instance/``. Copy ``instance/config.py.example`` to
``instance/config.py``. Replace the example configuration values with ones that
you want, primarily the Redis and Postgres connection details. The configuration
values are documented in the example configuration file. Leave ``instance/test_config.py``
alone, as it's meant to be used with the test suite.  

Environment
-----------
Pipenv is used for dependency and environment management. You can install it with
``pip install pipenv``. You will also need python 3.7 installed for this project.
Running ``pipenv install`` will set up a virtualenv and install the dependencies
listed in the ``Pipfile``.

Postgres and Redis are required services for this project. Install them from
your system's package manager or from source, it really doesn't matter as long
as they can pass the test suite. Create a database in Postgres, permission it,
and protect it. Do the same with Redis.  

Database
--------
Some default values will need to be set before running this project. We'll have an
installation script create these by default eventually. All new users will have a
User Class ID of 1. Therefore it is necessary that the lowest-tier User Class
also have that ID.

pulsar utilizes Alembic for its DB migrations. Alembic is built to work with SQLAlchemy
and has the ability to auto-generate migration (revision) files. If you are utilizing
Alembic's auto-generation function, please read
`Alembic's documentation <http://alembic.zzzcomputing.com/en/latest/autogenerate.html>`_.

Do not auto-migrate changes in table or column names. You will lose data; write those
migrations by hand.

Development
-----------
pulsar runs on the Flask micro-framework. Flask has great documentation, which can answer
most or all of your questions about the underlying framework objects used by core.

Code documentation, including the style guide, is available here:
https://sharebears.github.io/pulsar-docs/html/code/index.html.

A script to generate dummy data is located in ``scripts/dummy_test_data.py``. It will
drop all tables and recreate them per the current model schema, using the
``instance/config.py`` configuration. If there are more than 10 users in the database,
the script will error out, as a protection against accidental usage in production.  

Several development tools are used to maintain code quality.

- Our code linter is ``flake8``.
- We also use ``isort`` to lint and auto-sort import statements.
- ``pytest`` is used for testing.
- ``mypy`` is used for static type analysis.

Development commands and database migrations can be accessed through flask's
click cli interface.

- ``flask run`` runs the development server.In order to run in debug mode,
  run ``FLASK_DEBUG=True flask run`.
- ``flask db`` runs the ``flask-migrate`` database management script.

There are few things important things to keep in mind when developing this project

- All permission checks should be abstracted to a utility function, such as
  ``require_permission`` or ``choose_user``; or to the user model (``User.has_permission``).
- Individual model cache clears are taken care of upon database commit. When deleting
  or inserting an object, the cache key corresponding to lists containing the primary
  keys will need to be cleared manually. If someone can automate this without needless
  queries that would be great!
- Python typing is a meme and I regret implementing it. I am debating whether or not
  to remove it.
