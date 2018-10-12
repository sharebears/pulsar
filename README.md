# pulsar

A BitTorrent Indexer backend written using the Flask micro-framework.

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

### Development Intro

If you plan on developing this codebase, please read the following. pulsar is a RESTish
JSON API written in Flask, and structured in a way that facilitate ease of new module
creation / feature changes. Due to the magnitude of this project, pulsar has been split
up in a multi-repo pattern. Code necessary to run pulsar and some common abstractions /
base classes are present in the core repository--different parts of the site such as
forums, wikis, and requests are stored in their own repositories. These plugin packages
sum up to form a complete site API. Each of those plugins is a python package, and this
repository contains the "glue" which imports all of the plugin packages.

Package creation is fairly straightforward. Each package will have a very similar
structure to the others, and can use many of the same abstractions and base classes
present in the core. Existing packages can be used as a reference in case you are
confused. Here is an example directory structure (a lobotomized version of the forum
plugin).

```
. (pulsar-forums/)
├── forums
│   ├── __init__.py
│   ├── models.py
│   ├── modifications.py
│   ├── routes
│   │   ├── __init__.py
│   │   └── threads.py
│   └── serializers.py
├── .gitignore
├── LICENSE
├── Makefile
├── README.md
├── setup.cfg
├── setup.py
├── tests
│   ├── conftest.py
│   ├── __init__.py
│   ├── test_model_thread.py
│   └── test_view_threads.py
└── versions
    └── 29040202cb0d_init.py
```

To avoid terminology confusion, `plugin directory == pulsar-forums/` and `package
directory == pulsar-forums/forums`. `Installed` means installed with `pip` (these
packages can be installed with, for example, `pip(env)? install -e pulsar-forums`.

Each plugin must be prefixed with `pulsar-`. The forum plugin above is called
`pulsar-forums`. Inside each plugin there are some project files and three directories.
The project files will be consistent between plugin repositories, but the Makefile has to
be edited to point towards the package directory. The `setup.py` file is especially
important, but it does not need to be changed much plugin to plugin. The data must be
updated to reflect the new project name, and if there are any dependencies specific to
the plugin which aren't a part of the core, those must be added to `setup.py` file.
Having this file allows us to install the package to our systems or virtualenvs with
`pip`, which lets us import them into the glue repository or any dependent repositories.

Plugins can depend on other plugins, although no formal enforcement exists besides
`ImportError`'s. Please mention which other plugins your plugins are dependent on in the
README.

The `tests` directory contains all the unit tests for the plugin. The tests all require
the `pulsar-core` module to be installed. A single base conftest (a file that lets pytest
share code) is present in the core--it can be imported from `core.conftest`. In order to
have that run in your tests, several lines of code must be present in your conftest. A
template for your plugin's conftest is included below. The UNPOPULATE_DATABASE global
exists because while database population can be written as an `autouse=True` pytest
fixture in the plugin conftest, unpopulation after each test has to be performed inside a
specific fixture in `core.conftest`. For this reason you must define an
`unpopulate_database` function which deletes all the data you've put into the database
but doesn't drop the tables, and append that function to the `UNPOPULATE_FUNCTIONS`
global variable.

```python
from core.conftest import *  # noqa: F401, F403
from core.conftest import PLUGINS, UNPOPULATE_FUNCTIONS

import forums

@pytest.fixture(autouse=True)
def populate_db(client):  # `client` is a fixture from the core which opens up a DB connection.
   pass


def unpopulate_database(client):
   pass


PLUGINS.append(forums)
UNPOPULATE_FUNCTIONS.append(unpopulate_database)
```

Database migrations for each plugin are present in `versions/`. These are designed to
work with the `alembic` database migration tool, which hooks up with SQLAlchemy. Alembic
tracks revisions similar to how git tracks files--each revision has a parent (unless it
is a base revision). Each plugin is given its own revision branch too, from which all of
its future revisions can build off of. This allows us to maintain separate migration
histories for each individual plugin and manage them all from the glue repository.

```
Example usage of the migrations system to come. tl;dr there is a special command to set
up the migration branch, and all revisions which follow must specify the "head" revision
of the branch they belong to.
```

As stated before, each plugin package has a very similar structure. They should be named
succinctly, although if they clash with an existing or well-known python package you can
modify it's name to evade that. For example, the `pulsar-forums` plugin has the package
name `forums`. What goes inside each package will depend upon what you intend the package
to do.

If you want to add tables to the database, you should have a `models.py`. This file
contains all the database tables for the package, although they are defined as SQLAlchemy
objects which can be used in the codebase as an abstraction for the database data.

If you want any of those models to be returned via the API, you should have a
`serializers.py` file which defines serialization rules for models.

If you want to add properties/attributes to another dependent module, you should have a
`modifications.py` file, whose functions should in turn be imported into the package's
`__init__.py` and ran in the global scope.

If you want to add API endpoints, you should create a `routes/` directory and put your
routes inside it. The `__init__.py` file of the route must define a `bp` variable with a
`flask.Blueprint` value. That `bp` variable must also be imported from the `routes/`
package into the top-level package `__init__.py` in order for it to be registered by the
flask app.
