Models
======

Models provide a convenient object representation for rows in the database, as well as a 
convenient way to access related objects by Foreign Keys. Most models will subclass one 
or more mixins, which provide convenient abstractions for commonly used methods. However, 
compared to classic SQLAlchemy models, pulsar's may be larger and require more manual 
code. In order to take advantage of caching at a model level, we do not define 
``relationship``'s, instead opting to create properties which return other models with 
their methods which support caching. Caching is handled by the mixins subclassed by 
models.

``@property``'s are used to add attributes to models which are not part of their SQL 
schema. ``@cached_property`` is an alternative ``@property`` which caches the value in a 
private variable and should be used for any properties that do not change during the 
lifetime of a request.

Users
-----

.. automodule:: core.users.models
    :members:
    :show-inheritance:

Permissions
-----------

.. automodule:: core.permissions.models
    :members:
    :show-inheritance:

Forums
------

.. automodule:: forums.models
    :members:
    :show-inheritance:
