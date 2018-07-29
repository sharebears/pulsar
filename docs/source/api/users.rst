Users
=====

.. qrefflask:: pulsar:create_app('config.py')
   :undoc-static:
   :blueprints: users
   :order: path

Users
-----

.. autoflask:: pulsar:create_app('config.py')
   :undoc-static:
   :modules: pulsar.users.users
   :groupby: view
   :order: path

API Keys
--------
pulsar supports token (API key) authentication. API keys are generated on
request, and must be manually granted permissions (blank for full permissions).
To authenticate with an API key, send it in the request header as
``Authorization: Token a-long-api-key``.

.. autoflask:: pulsar:create_app('config.py')
   :undoc-static:
   :modules: pulsar.users.api_keys
   :groupby: view
   :order: path

Invites
-------

.. autoflask:: pulsar:create_app('config.py')
   :undoc-static:
   :modules: pulsar.users.invites
   :groupby: view
   :order: path

Settings
--------

.. autoflask:: pulsar:create_app('config.py')
   :undoc-static:
   :modules: pulsar.users.settings
   :groupby: view
   :order: path

Moderation
----------

.. autoflask:: pulsar:create_app('config.py')
   :undoc-static:
   :modules: pulsar.users.moderate
   :groupby: view
   :order: path
