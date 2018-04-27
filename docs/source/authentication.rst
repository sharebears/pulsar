Authentication Endpoint
=======================

.. qrefflask:: pulsar:create_app('config.py')
   :undoc-static:
   :include-empty-docstring:
   :blueprints: auth
   :order: path

Login
-----

.. autoflask:: pulsar:create_app('config.py')
   :undoc-static:
   :include-empty-docstring:
   :modules: pulsar.auth.views.login
   :order: path

API Keys
--------

.. autoflask:: pulsar:create_app('config.py')
   :undoc-static:
   :include-empty-docstring:
   :modules: pulsar.auth.views.api_keys
   :groupby: view
   :order: path

Sessions
--------

.. autoflask:: pulsar:create_app('config.py')
   :undoc-static:
   :include-empty-docstring:
   :modules: pulsar.auth.views.sessions
   :order: path
