Installation & Development
==========================

Config
------
An explanation of configuration options is available in ``config.py.example``. All
configurations should be placed in ``instance/``. A unique secret key with high entropy can be generated with ``os.urandom``.

Initial DB values
-----------------
By default, all users will have a User Class ID of 1. Therefore it is necessary that
the lowest-tier User Class also have that ID.

Running the server
------------------
You can use uWSGI or Gunicorn to run pulsar in production. Flask's built in server is
only useful for development.

Development
-----------
pulsar runs on the Flask micro-framework. It has great documentation. Read it.

* All permission checks should be abstracted to a utility function, such as
  ``require_permission``, ``require_auth``, or ``choose_user``; or to the user model
  (``User.has_permission``).

DB Migrations
-------------
pulsar utilizes Alembic for its DB migrations. Alembic is built to work with SQLAlchemy
and has the ability to auto-generate migration (revision) files. If you are utilizing
Alembic's auto-generation function, please read
`Alembic's documentation <http://alembic.zzzcomputing.com/en/latest/autogenerate.html>`_.

.. warning ::

   Do not auto-migrate changes in table or column names. You will lose data; write those
   migrations by hand.
