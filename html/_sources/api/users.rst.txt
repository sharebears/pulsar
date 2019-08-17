Users
=====

.. qrefflask:: wsgi:create_app('config.py')
   :undoc-static:
   :blueprints: users.routes
   :order: path

API Keys
--------
pulsar supports token (API key) authentication. API keys are generated on
request, and must be manually granted permissions (blank for full permissions).
To authenticate with an API key, send it in the request header as
``Authorization: Token a-long-api-key``.

.. autoflask:: wsgi:create_app('config.py')
   :undoc-static:
   :modules: core.users.routes.api_keys
   :groupby: view
   :order: path

Invites
-------

.. autoflask:: wsgi:create_app('config.py')
   :undoc-static:
   :modules: core.users.routes.invites
   :groupby: view
   :order: path

Settings
--------

.. autoflask:: wsgi:create_app('config.py')
   :undoc-static:
   :modules: core.users.routes.settings
   :groupby: view
   :order: path

Users
-----

.. autoflask:: wsgi:create_app('config.py')
   :undoc-static:
   :modules: core.users.routes.users
   :groupby: view
   :order: path

Moderation
----------

.. autoflask:: wsgi:create_app('config.py')
   :undoc-static:
   :modules: core.users.routes.moderate
   :groupby: view
   :order: path
