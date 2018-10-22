# pulsar

A BitTorrent Indexer backend written using the Flask micro-framework.


## Getting started (without Docker)

### Requirements:

- Python3.7
- pyenv: https://github.com/pyenv/pyenv
- pipenv: https://github.com/pypa/pipenv


### Building the project

- Install python dependencies:

```bash
pipenv install --dev
```

- Rename config.py.example to config.py

```bash
cp /instance/config.py.example /instance/config.py
```

- Make sure Postgres and Redis are installed and running, and modify the configs in config.py to match them.

- Enter the pipenv virtual environment:

```bash
pipenv shell
```

- Create empty db tables

```bash
flask dev createdb
```

- Run the app from within the pipenv shell

```bash
flask run
```

## API Documentation
https://sharebears.github.io/pulsar-docs/html/index.html

## About Pulsar

Pulsar is a RESTish JSON API written in Flask, and structured in a way that facilitate 
ease of new module creation / feature changes. Due to the magnitude of this project, 
pulsar has been split up in a multi-repo pattern. Code necessary to run pulsar and some 
common abstractions / base classes are present in the core repository--different parts of 
the site such as forums, wikis, and requests are stored in their own repositories. These 
plugin packages sum up to form a complete site API. Each of those plugins is a python 
package, and this repository contains the "glue" which imports all of the plugin 
packages. Modules are tracked as git submodules in the `plugins/` directory. They are installed as editable python packages in
pulsar's pipenv.

You should fork or branch this repository for your own needs. It is meant to serve as a
basic repository for controlling plugins, handling database migrations, and running the
site. Configuration options for all plugins are also handled in this repository. All
configuration files can be found in `instance/`. An explanation of `core` configuration
options is present in `config.py.example`. Configuration options for each plugin can be
found in their documentation. To create your own config file, copy
`instance/config.py.example` to `instance/config.py` and replace the configuration values
with your own values. This must be done for the connection details to various services.

`postgresql` and `redis` are used to store and cache data. They must be installed and
accessible--the connection details must be specified in the config file. It is up to you
to configure the databases, but note that a database named `pulsar-testing` must exist to
run the test suite.

Pulsar assumes that the lowest-tier `UserClass` has an ID of 1. Therefore, you must
assign the lowest-tier `UserClass` the ID 1.

Database migrations are handled via `Flask-Migrate`, a wrapper around `Alembic`. To
accommodate the multi-repo, each plugin has its own branch in alembic, which allows
collinear migrations to be made with references and dependencies on each other. Alembic
is built to work with SQLAlchemy and has the ability to auto-generate migration
(revision) files. If you are utilizing Alembic's auto-generation function, please read
[Alembic's documentation](<http://alembic.zzzcomputing.com/en/latest/autogenerate.html>).
When creating revisions, you will need to specify which branch to add the migration to.

**Warning:** Do not auto-migrate changes in table or column names. You will lose data;
write those migrations by hand.

### Contributions

Contributed code must follow the style guide (included in the documentation), contain a
test suite, and be properly documented.

You can access many commands via flask's CLI interface. `flask run` will run the site;
`FLASK_DEBUG=True flask run` runs the site in debug mode. `flask db` reveals the database
migration interface. In general you can simply type `flask` in the command line to see available options.
