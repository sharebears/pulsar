# pulsar

A BitTorrent Indexer backend written using the Flask micro-framework.

RTFD: https://sharebears.github.io/pulsar-docs/html/index.html

This repository is merely the glue repository which ties the project together. pulsar has
been built using a multi-repo project structure, meaning you can select the modules which
you want to load and exclude the ones you do not want to load. Modules are tracked as git
submodules in the `plugins/` directory. They are installed as editable python packages in
pulsar's pipenv.

You should fork or branch this repository for your own needs. It is meant to serve as a
basic repository for controlling plugins, handling database migrations, and running the
site. Configuration options for all plugins are also handled in this repository. All
configuration files can be found in `instance/`. An explanation of `core` configuration
options is present in `config.py.example`. Configuration options for each plugin can be
found in their documentation. To create your own config file, copy
`instance/config.py.example` to `instance/config.py` and replace the configuration values
with your own values. This must be done for the connection details to various services.

Setting up the environment is fairly simple. You will need python 3.7 installed on your
system. It does not need to be the default python version or installed for the
system--using a version installed with `pyenv` works fine. `Pipenv` is used to manage
dependencies and virtualenv. You will need `pipenv` installed on your computer and
somewhere in your \$PATH. Run `pipenv install` in the top-level directory of the
repository to create the virtualenv and install all dependencies. If you intend to
develop the codebase, run `pipenv install --dev`, which will install the tools necessary
to run the tests. Note: If you have pyenv installed and pipenv does not detect python
3.7, it will install python 3.7 via pyenv and use it.

`postgresql` and `redis` are used to store and cache data. They must be installed and
accessible--the connection details must be specified in the config file. It is up to you
to configure the databases, but note that a database named `pulsar-testing` must exist to
run the test suite.

pulsar assumes that the lowest-tier `UserClass` has an ID of 1. Therefore, you must
assign the lowest-tier `UserClass` the ID 1.

Database migrations are handled via `Flask-Migrate`, a wrapper around `Alembic`. To
accommodate the multi-repo, each plugin has its own branch in alembic, which allows
collinear migrations to be made with references and dependencies on each other. Alembic
is built to work with SQLAlchemy and has the ability to auto-generate migration
(revision) files. If you are utilizing Alembic's auto-generation function, please read
[Alembic's documentation](<http://alembic.zzzcomputing.com/en/latest/autogenerate.html>).
When creating revisions, you will need to specify which branch to add the migration to.

TODO: db create all command to get the database up to date.

**Warning:** Do not auto-migrate changes in table or column names. You will lose data;
write those migrations by hand.

### Contributions

Contributed code must follow the style guide (included in the documentation), contain a
test suite, and be properly documented.

A script to generate dummy data is located in `scripts/dummy_test_data.py`. It will
drop all tables and recreate them per the current model schema, using the
`instance/config.py` configuration. If there are more than 10 users in the database,
the script will error out, as a protection against accidental usage in production.

You can access many commands via flask's CLI interface. `flask run` will run the site;
`FLASK_DEBUG=True flask run` runs the site in debug mode. `flask db` reveals the database
migration interface.

pulsar is a RESTish JSON API written in Flask, and structured in a way that facilitate 
ease of new module creation / feature changes. Due to the magnitude of this project, 
pulsar has been split up in a multi-repo pattern. Code necessary to run pulsar and some 
common abstractions / base classes are present in the core repository--different parts of 
the site such as forums, wikis, and requests are stored in their own repositories. These 
plugin packages sum up to form a complete site API. Each of those plugins is a python 
package, and this repository contains the "glue" which imports all of the plugin 
packages.
