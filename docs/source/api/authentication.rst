Authentication
==============

pulsar supports session-based and token (API key) authentication. Sessions are
created by logging in with a username and password, and have full permissions
access. All state modifying requests done with session-based authentication
must also carry an accompanying ``csrf_token``. API keys are generated on
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

Sessions
--------

.. autoflask:: pulsar:create_app('config.py')
   :undoc-static:
   :modules: pulsar.auth.sessions
   :groupby: view
   :order: path

API Keys
--------

.. autoflask:: pulsar:create_app('config.py')
   :undoc-static:
   :modules: pulsar.auth.api_keys
   :groupby: view
   :order: path
