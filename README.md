# pulsar
A BitTorrent Indexer API written in python using the Flask micro-framework.
Pipenv is used for dependency management.  

The current roadmap of To-Dos is located in ROADMAP.md.  


## Environment
Pipenv is used for dependency and environment management, and is needed
for pulsar's dependency management. You can install it with `pip install pipenv`.
You will also need python 3.6 installed somewhere on your system. Use pyenv
or something, idk, someone will need to help describe that process for me.
Run `pipenv install` in the project directory (`pulsar/`) to initialize the project,
and use `pipenv shell` to activate the virtualenv.  

Postgres and Redis are required services for this project. Install them from
your system's package manager or from source, it really doesn't matter as long
as they can pass the test suite. Create a database in Postgres, permission it,
and protect it. Do the same with Redis.  

Configuration files are located in `instance/`. Copy `instance/config.py.example` to
`instance/config.py`. Replace the example configuration values with ones that
you want, primarily the Redis and Postgres connection details. The configuration
values are documented in the example configuration file. Leave `instance/test_config.py`
alone, as it's meant to be used with the test suite.  

A script to generate dummy data is located in `scripts/dummy_test_data.py`. It will
drop all tables and recreate them per the current model schema, using the
`instance/config.py` configuration. If there are more than 10 users in the database,
the script will error out, as a protection against accidental usage in production.  


## Development Tools
Several development tools are employed to maintain code quality. `flake8` is used
for linting, `mypy` for static type analysis, `isort` for import ordering, and
`pytest` & `pytest-cov` for testing. Test and lint your code before submitting
merge requests!  

Development commands and database migrations can be accessed through flask's
click cli interface. `flask run` runs the development server and `flask db` runs
the `flask-migrate` database management script. More detail about these commands
and the development environment will be located in the `Installation & Development`
section of the docs.


## Links of Interest
* [Installation & Development](docs/source/code/hacking.rst)  
* [Style Guide](docs/source/code/style.rst)  
