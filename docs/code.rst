Code
====

Given the size of this project, it may be daunting to jump in and start developing. In
order to make it easier to get started and understand the codebase, the following
documentation will go over design choices, the reasoning behind them, how they work, and
effectively leveraging existing code.

pulsar runs with a multi-repo structure. The core functionality, abstractions, and base
classes has been placed into a core package, and everything else is made available as a
plugin. This has been done to allow trackers deriving from pulsar to select which plugins
they want to include. If one tracker doesn't want bonus points, for example, they need
not load the plugin. The core package is treated itself as another plugin, although it's
inclusion in a working install of pulsar is mandatory. pulsar provides a basic "glue"
repository, which is where the various plugins are installed and coordinated. That
repository contains the code that spawns the Flask app, as well as documentation and a
system to handle database migrations for all installed plugins. Handling plugins will be
covered later on in the documentation.

Since pulsar is the backend API, it is very database-oriented. Most of the code goes
towards managing data which goes to the database or fetching data from the database.
Managing data is handled by SQLAlchemy model classes, which have attributes that match
with columns in a database table. One model class is defined for each table, except for
many-to-many relationship tables. Each model class contains methods which allow for easy
access of data and related data or input of data. The model classes are used in the
routes, which are the API endpoints that handle requests for data. Adding new features to
the codebase will usually require creating models and views. The boilerplate which
augments models and views with simple abstractions, caching, and permissions is
contained in the core.

The Glue Repository
-------------------

The glue repository contains very little code, but most of the project management tools
and files. There are 4 top-level directories in the glue repository: ``instance``,
``migrations``, ``plugins``, and ``scripts``.

* ``instance`` contains the configuration files--that's where an instance of the codebase
  is configured.

* ``migrations`` doesn't actually house any of the database migrations, but rather the
  configuration files for alembic, which manages the database migrations. Database
  migrations are stored in each plugin, and since the glue repository has almost no code
  it has no migrations of its own.

* ``plugins`` contains all the installed plugins.

* ``scripts`` contains some development tools.

The Core Package
----------------

The core package contains everything essential for the codebase, as well as base classes
shared across multiple major plugins. Along with the boilerplate and response handling
code, the users, authentication, and permissions systems are included in it. Much of the
code is localized to the core--rarely will an external plugin need to modify the pre- and
post- response hooks, the caching system, or the object serialization system.

Server-Side Caching
-------------------

Even with all of Gazelle's faults, it still made a good choice in caching data. Trackers
store a lot of data and users make many requests to the site, leading to heavy data
fetching and rendering. Site load is no joke, and to keep the tracker running smoothly
Redis is utilized to store recently-accessed data in RAM. Instead of fetching the same
data from the database over and over again, we can make use of RAM and only fetch new
data from the database when something changes. In pulsar, caching is heavily
abstracted–the majority of cache work is done behind the scenes in the model mixins and
cache module. It is due to this caching system that pulsar does not load data from
relationship objects in its SQLAlchemy models. At the cost of a few more lines of code,
objects related to each model can be loaded from the cache, due to the caching code
present inside the mixins loaded into almost every model.

Caching can sometimes result in out of date data, but steps are taken against that 
happening in core. Whenever a model is modified and flushed to the database, a listener 
(``clear_cache_dirty``, found in ``core.cache``) will automatically expire its cache key. 
The only keys which need to be explicitly expired in a view or model are the cache keys 
for lists of models, which are typically lists of their primary keys. Cache keys are 
defined based on attributes of the model and their primary keys, so they can also be 
expired manually.

Plugin Creation
---------------

Package creation is fairly straightforward. Each package will have a very similar
structure to the others, and can use many of the same abstractions and base classes
present in the core. Existing packages can be used as a reference in case you are
confused. Here is an example directory structure (a lobotomized version of the forum
plugin).

.. parsed-literal::
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

To avoid terminology confusion, ``plugin directory == pulsar-forums/`` and ``package
directory == pulsar-forums/forums``. ``Installed`` means installed with ``pip`` (these
packages can be installed with, for example, ``pip(env)? install -e pulsar-forums``.

Each plugin must be prefixed with ``pulsar-``. The forum plugin above is called
``pulsar-forums``. Inside each plugin there are some project files and three directories.
The project files will be consistent between plugin repositories, but the Makefile has to
be edited to point towards the package directory. The ``setup.py`` file is especially
important, but it does not need to be changed much plugin to plugin. The data must be
updated to reflect the new project name, and if there are any dependencies specific to
the plugin which aren't a part of the core, those must be added to ``setup.py`` file.
Having this file allows us to install the package to our systems or virtualenvs with
``pip``, which lets us import them into the glue repository or any dependent repositories.

Plugins can depend on other plugins, although no formal enforcement exists besides
``ImportError``'s. Please mention which other plugins your plugins are dependent on in the
README.

The ``tests`` directory contains all the unit tests for the plugin. The tests all require
the ``pulsar-core`` module to be installed. A single base conftest (a file that lets pytest
share code) is present in the core--it can be imported from ``core.conftest``. In order to
have that run in your tests, several lines of code must be present in your conftest. A
template for your plugin's conftest is included below. The UNPOPULATE_DATABASE global
exists because while database population can be written as an ``autouse=True`` pytest
fixture in the plugin conftest, unpopulation after each test has to be performed inside a
specific fixture in ``core.conftest``. For this reason you must define an
``unpopulate_database`` function which deletes all the data you've put into the database
but doesn't drop the tables, and append that function to the ``UNPOPULATE_FUNCTIONS``
global variable.

.. code-block:: python

   from core.conftest import *  # noqa: F401, F403
   from core.conftest import PLUGINS, UNPOPULATE_FUNCTIONS

   import forums

   @pytest.fixture(autouse=True)
   def populate_db(client):  # ``client`` is a fixture from the core which opens up a DB 
   connection.
      pass


   def unpopulate_database(client):
      pass


   PLUGINS.append(forums)
   UNPOPULATE_FUNCTIONS.append(unpopulate_database)

Database migrations for each plugin are present in ``versions/``. These are designed to
work with the ``alembic`` database migration tool, which hooks up with SQLAlchemy. Alembic
tracks revisions similar to how git tracks files--each revision has a parent (unless it
is a base revision). Each plugin is given its own revision branch too, from which all of
its future revisions can build off of. This allows us to maintain separate migration
histories for each individual plugin and manage them all from the glue repository.

Example usage of the migrations system to come. tl;dr there is a special command to set
up the migration branch, and all revisions which follow must specify the "head" revision
of the branch they belong to.

As stated before, each plugin package has a very similar structure. They should be named
succinctly, although if they clash with an existing or well-known python package you can
modify it's name to evade that. For example, the ``pulsar-forums`` plugin has the package
name ``forums``. What goes inside each package will depend upon what you intend the package
to do.

If you want to add tables to the database, you should have a ``models.py``. This file
contains all the database tables for the package, although they are defined as SQLAlchemy
objects which can be used in the codebase as an abstraction for the database data.

If you want any of those models to be returned via the API, you should have a
``serializers.py`` file which defines serialization rules for models.

If you want to add properties/attributes to another dependent module, you should have a
``modifications.py`` file, whose functions should in turn be imported into the package's
``__init__.py`` and ran in the global scope.

If you want to add API endpoints, you should create a ``routes/`` directory and put your
routes inside it. The ``__init__.py`` file of the route must define a ``bp`` variable with a
``flask.Blueprint`` value. That ``bp`` variable must also be imported from the ``routes/``
package into the top-level package ``__init__.py`` in order for it to be registered by the
flask app.

Mixins in SQLAlchemy Models
---------------------------

The mixins used by pulsar's SQLAlchemy models provide methods which abstract a lot of
the code required to query for an object. On top of that, it implements code that
automatically caches every fetched model, and whenever a model is requested, it's first
checked against the cache before being queried from the database. If a model is found in
the cache, it will be loaded from there instead of from the database, saving a call.

Generic Mixins
^^^^^^^^^^^^^^

There are two generic mixins: ``SinglePKMixin`` and ``MultiPKMixin``. Their uses can be
inferred from their names: ``SinglePKMixin`` is for objects which have a single unique
attribute, such as users, and ``MultiPKMixin`` is geared towards objects which do not,
such as a permission (uniquely identified by user and permission). The above two mixins
are documented below:

.. automodule:: core.mixins.single_pk
    :members:
    :show-inheritance:
    :special-members:
    :private-members:

.. automodule:: core.mixins.multi_pk
    :members:
    :show-inheritance:
    :special-members:
    :private-members:

Specialized Mixins
^^^^^^^^^^^^^^^^^^

In pulsar, there are many similar yet slightly different models, such as ``UserClass`` and
``SecondaryUserClass``. Since code reuse is great and copy/paste not so much, there are
a few mixins in the core package which provide the attributes and functions ubiquitous to
all models of a certain nature.

.. automodule:: core.mixins.class_
    :members:
    :show-inheritance:
    :special-members:
    :private-members:

.. automodule:: core.mixins.permission
    :members:
    :show-inheritance:
    :special-members:
    :private-members:

JSON Serialization
------------------

pulsar allows for model objects to be passed into ``flask.jsonify``, for the purposes of
convenience (no need to serialize every object in a nested structure before passing it
into ``flask.jsonify``). It does this by modifying Flask's ``JSONEncoder`` attribute and
accessing the ``Serializer`` object assigned to a model's ``__serializer__`` attribute.

Each model which can be returned in the API must have a serializer. Serializer classes
subclass the ``Serializer`` mixin (documented below), and contain attributes of the
``Attribute`` type. The code which handles the serialization of models and other types is
found in ``core.serializer``.

.. automodule:: core.mixins.serializer
    :members:
    :show-inheritance:
    :special-members:
    :private-members:

Exceptions
----------

These are python exceptions that mirror HTTP errors. When raised they will trigger the 
matching HTTP error and a JSON response.

.. automodule:: core.exceptions
    :members:
    :show-inheritance:
    :private-members:

Request Hooks
-------------

These hooks run before and after each request gets sent to a controller, taking care of 
various checks and overrides that apply to every view.

Before
^^^^^^

Before relaying the request to its proper controller, check the authentication of the 
requester, via API key. If the requester has the ``no_ip_history`` permission, set their 
IP to ``0.0.0.0``. 

.. automodule:: core.hooks.before
    :members:
    :show-inheritance:

After
^^^^^

After receiving a response from the controller, wrap it in a homogenized response 
dictionary and serialize it to JSON. The response dictionary will have a ``status`` key 
and, if the request came with session based authentication, a CRSF token.

.. automodule:: core.hooks.after
    :members:
    :show-inheritance:

Validator Functions
-------------------

Users
^^^^^

.. automodule:: core.validators.users
    :members:
    :show-inheritance:

Permissions
^^^^^^^^^^^

.. automodule:: core.validators.permissions
    :members:
    :show-inheritance:

Posts
^^^^^

.. automodule:: core.validators.posts
    :members:
    :show-inheritance:

Utility Functions
-----------------

Permissions
^^^^^^^^^^^

.. automodule:: core.utils.permissions
    :members:
    :show-inheritance:

Validation
^^^^^^^^^^

.. automodule:: core.utils.validation
    :members:
    :show-inheritance:

Memoization
^^^^^^^^^^^

.. automodule:: core.utils.memoization
    :members:
    :show-inheritance:
