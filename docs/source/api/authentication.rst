Authentication
==============

pulsar supports token (API key) authentication. API keys are generated on
request, and must be manually granted permissions (blank for full permissions).
To authenticate with an API key, send it in the request header as
``Authorization: Token a-long-api-key``.

.. qrefflask:: pulsar:create_app('config.py')
   :undoc-static:
   :blueprints: auth
   :order: path

Login
-----

.. autoflask:: pulsar:create_app('config.py')
   :undoc-static:
   :modules: pulsar.auth.login
   :groupby: view
   :order: path

API Keys
--------

.. autoflask:: pulsar:create_app('config.py')
   :undoc-static:
   :modules: pulsar.auth.api_keys
   :groupby: view
   :order: path
