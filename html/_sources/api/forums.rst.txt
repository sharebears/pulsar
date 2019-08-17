Forums
======

.. qrefflask:: wsgi:create_app('config.py')
   :undoc-static:
   :blueprints: forums.routes
   :order: path

Categories
----------

.. autoflask:: wsgi:create_app('config.py')
   :undoc-static:
   :modules: forums.routes.categories
   :groupby: view
   :order: path

Forums
------

.. autoflask:: wsgi:create_app('config.py')
   :undoc-static:
   :modules: forums.routes.forums
   :groupby: view
   :order: path

Threads
-------

.. autoflask:: wsgi:create_app('config.py')
   :undoc-static:
   :modules: forums.routes.threads
   :groupby: view
   :order: path

Posts
-----

.. autoflask:: wsgi:create_app('config.py')
   :undoc-static:
   :modules: forums.routes.posts
   :groupby: view
   :order: path

Polls
-----

.. autoflask:: wsgi:create_app('config.py')
   :undoc-static:
   :modules: forums.routes.polls
   :groupby: view
   :order: path
