import flask
from datetime import datetime
from flask_sqlalchemy import Model
from sqlalchemy.orm.session import make_transient_to_detached


class PulsarModel(Model):
    """
    This is a custom model for the pulsar project, which adds caching
    and JSON serialization methods to the base model. Subclasses are
    expected to define their serializable attributes, permission restrictions,
    and cache key template with the following class attributes. They are required
    if one wants to cache or serialize data for a model.

    * ``__cache_key__`` (``str``)
    * ``__serialize__`` (``tuple``)
    * ``__serialize_self__`` (``tuple``)
    * ``__serialize_detailed__`` (``tuple``)
    * ``__serialize_very_detailed__`` (``tuple``)
    * ``__serialize_nested_exclude__`` (``tuple``)
    * ``__permission_detailed__`` (``str``)
    * ``__permission_very_detailed__`` (``str``)

    When a model is serialized, the permissions assigned to a user and the
    permissions listed in the above attributes will determine which properties
    of the model are returned. ``__serialize__`` is viewable to anyone with permission
    to see the resource, ``__serialize_self__`` is viewable by anyone who passes the
    ``belongs_to_user`` function. ``__serialize_detailed__`` and
    ``__serialize_very_detailed__`` are viewable by users with the permission ``str``s
    stored as ``__permission_detailed__`` and ``__permission_very_detailed__``,
    respectively.

    Nested model properties will also be serialized if they are the value of a ``dict``
    or in a ``list``. When nested models are serialized, all attributes listed in
    ``__serialize_nested_exclude__`` will be excluded.
    """

    __serialize__ = tuple()
    __serialize_self__ = tuple()
    __serialize_detailed__ = tuple()
    __serialize_very_detailed__ = tuple()
    __serialize_nested_exclude__ = tuple()

    __permission_detailed__ = None
    __permission_very_detailed__ = None

    def belongs_to_user(self):
        """
        Function to determine whether or not the model "belongs" to a user
        by comparing against flask.g.user. This is meant to be overridden
        by subclasses, and returns False by default (if not overridden).

        :return: ``True`` if "belongs to user", else ``False``
        """
        return False

    @classmethod
    def from_cache(cls, key, query=None):
        """
        Check the cache for an instance of this model and attempt to load
        its attributes from the cache instead of from the database.
        If found, the object is merged into the database session and returned.

        :param str key: The cache key to get
        :return: The uncached ``PulsarModel`` or ``None``
        """
        from pulsar import db, cache
        data = cache.get(key)
        if data:
            if cls._valid_data(data):
                obj = cls(**data)
                make_transient_to_detached(obj)
                obj = db.session.merge(obj, load=False)
                return obj
            else:
                cache.delete(key)
        if query:
            obj = query.first()
            cache.cache_model(obj)
            return obj
        return None

    @classmethod
    def _valid_data(cls, data):
        """ Check the validity of data being passed to a function by making sure that
        all of its cacheable attributes are being loaded.

        :param dict data: The stored object data to validate

        :return: ``True`` if valid or ``False`` if invalid
        """
        if not isinstance(data, dict):
            return False
        return not set(data.keys()) != set(cls.__table__.columns.keys())

    def clear_cache(self):
        """Clear the cache key for this instance of a model."""
        from pulsar import cache
        cache.delete(self.cache_key)

    def to_dict(self, nested=False):
        """
        Convert the model to a dictionary based on its defined serializable attributes.
        ``PulsarModel`` objects embedded in the dictionary or lists in the dictionary
        will be replaced with the result of their ``to_dict`` methods.

        :param bool detailed: Whether or not to include detailed serializable attributes
        :param bool very_detailed: Whether or not to include very detailed serializable attributes

        :return: The ``dict`` of serialized attributes
        """
        attrs = self.__serialize__
        if self.belongs_to_user():
            attrs += self.__serialize_self__
        if flask.g.user and flask.g.user.has_permission(self.__permission_detailed__):
            attrs += self.__serialize_detailed__
        if flask.g.user and flask.g.user.has_permission(self.__permission_very_detailed__):
            attrs += self.__serialize_very_detailed__
        if nested:
            attrs = [a for a in attrs if a not in self.__serialize_nested_exclude__]

        print(attrs)
        return self._objects_to_dict(
            {attr: getattr(self, attr, None) for attr in list(set(attrs))})

    def _objects_to_dict(self, dict_):
        """
        Iterate through all values inside a dictionary and "fix" a dictionary to be
        JSON serializable by applying the to_dict() function to all embedded models.
        All datetime objects are converted to a POSIX timestamp (seconds since epoch).

        :param dict dict_: The dictionary to iterate over and make JSON serializable

        :return: A JSON serializable ``dict``
        """
        for k, v in dict_.items():
            if isinstance(v, dict):
                dict_[k] = self._objects_to_dict(v)
            elif isinstance(v, list):
                v = [*v]  # Strip SQLA InstrumentedList
                for i, v2 in enumerate(v):
                    if isinstance(v2, PulsarModel):
                        v[i] = v2.to_dict()
                    elif isinstance(v2, dict):
                        v[i] = self._objects_to_dict(v2)
                dict_[k] = v
            elif isinstance(v, PulsarModel):
                dict_[k] = v.to_dict(nested=True)
            elif isinstance(v, datetime):
                dict_[k] = int(v.timestamp())

        return dict_
