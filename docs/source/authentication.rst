Authentication
==============

.. qrefflask:: pulsar:create_app('config.py')
   :undoc-static:
   :blueprints: auth
   :order: path

Login
-----

.. autoflask:: pulsar:create_app('config.py')
   :undoc-static:
   :modules: pulsar.auth.views.login
   :groupby: view
   :order: path

Sessions
--------

.. autoflask:: pulsar:create_app('config.py')
   :undoc-static:
   :modules: pulsar.auth.views.sessions
   :groupby: view
   :order: path

API Keys
--------

.. autoflask:: pulsar:create_app('config.py')
   :undoc-static:
   :modules: pulsar.auth.views.api_keys
   :groupby: view
   :order: path
