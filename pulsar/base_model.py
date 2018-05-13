from flask_sqlalchemy import Model
from sqlalchemy import func
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
    * ``__serialize_nested_include__`` (``tuple``)
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
    ``__serialize_nested_exclude__`` will be excluded, while all attributes in
    ``__serialize_nested_include__`` will be included.
    """

    __cache_key__ = None

    __serialize__ = tuple()
    __serialize_self__ = tuple()
    __serialize_detailed__ = tuple()
    __serialize_very_detailed__ = tuple()
    __serialize_nested_include__ = tuple()
    __serialize_nested_exclude__ = tuple()

    __permission_detailed__ = None
    __permission_very_detailed__ = None

    @property
    def cache_key(self):
        """Default property for cache key, override if not formatted by ID."""
        return self.__cache_key__.format(id=self.id)

    @classmethod
    def from_id(cls, id, *, include_dead=False):
        """
        Default classmethod constructor to get an object by its PK ID.
        If the object has a deleted/revoked/expired column, it will compare a
        ``include_dead`` kwarg against it.

        :param int id: The primary key ID of the object to query for.

        :return: A ``PulsarModel`` model or ``None``.
        """
        model = cls.from_cache(
            key=cls.__cache_key__.format(id=id),
            query=cls.query.filter(cls.id == id))
        if model:
            if include_dead or not (
                    getattr(model, 'deleted', False)
                    or getattr(model, 'revoked', False)
                    or getattr(model, 'expired', False)):
                return model
        return None

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
    def get_many(cls, *, key, filter=None, order=None, required_properties=tuple(),
                 include_dead=False, page=None, limit=None):
        """
        Abstraction function to get a list of IDs from the cache with a cache
        key, and query for those IDs if the key does not exist. If the query
        needs to be ran, a list will be created from the first element in
        every returned tuple result, like so:
            ``[x[0] for x in cls.query.all()]``

        That list will be converted into models, using the keyword arguments to
        modify which elements are included and which aren't. Pagination is optional
        and ignored if neither page nor limit is set.

        :param str key: The cache key to check (and return if present)
        :param filter: A SQLAlchemy filter expression to be applied to the query
        :param order: A SQLAlchemy order_by expression to be applied to the query
        :param required_properties: Properties required to validate to ``True``
            for a retrieved item to be included in the returned list
        :param bool include_dead: Whether or not to include deleted/revoked/expired
            models
        :param int page: The page number of results to return
        :param int limit: The limit of results to return, defaults to 50 if page
            is set, otherwise infinite
        """
        from pulsar import db, cache
        ids = cache.get(key)
        if not ids:
            query = cls._construct_query(db.session.query(cls.id), filter, order)
            ids = [x[0] for x in query.all()]
            cache.set(key, ids)

        if page is not None:
            limit = limit or 50
            ids = ids[(page - 1) * limit:]

        models = []
        num_models = 0
        for id in ids:
            model = cls.from_id(id, include_dead=include_dead)
            if model:
                for prop in required_properties:
                    if not getattr(model, prop, False):
                        break
                else:
                    models.append(model)
                    num_models += 1
                    if limit and num_models >= limit:
                        break
        return models

    @classmethod
    def _valid_data(cls, data):
        """ Check the validity of data being passed to a function by making sure that
        all of its cacheable attributes are being loaded.

        :param dict data: The stored object data to validate

        :return: ``True`` if valid or ``False`` if invalid
        """
        if not isinstance(data, dict):
            return False
        return set(data.keys()) == set(cls.__table__.columns.keys())

    @classmethod
    def new(cls, **kwargs):
        """
        Create a new instance of the model, add it to the instance, cache it,
        and return it.

        :param kwargs: The new attributes of the model.
        """
        from pulsar import db, cache
        model = cls(**kwargs)
        db.session.add(model)
        db.session.commit()
        cache.cache_model(model)
        return model

    def get_one(self, *, key, model, filter=None, order=None):
        """
        Function to get a single object from the database (limit(1), first()).
        Getting the object via the provided cache key will be attempted first; if
        it does not exist, then a query will be constructed with the other
        parameters. The resultant object (if exists) will be cached and returned.

        *The queried model must have a primary key column named ``id`` and a
        ``from_id`` classmethod constructor.*

        :param str key: The cache key to check
        :param PulsarModel model: The model to query
        :param filter: A SQLAlchemy expression to filter the query with
        :param order: A SQLAlchemy expression to order the query by

        :return: A ``PulsarModel`` object of the ``model`` class, or ``None``
        """
        from pulsar import cache
        model_id = cache.get(key)
        if not model_id:
            query = self._construct_query(model.query, filter, order)
            model = query.limit(1).first()
            if model:
                if not cache.has(model.cache_key):
                    cache.cache_model(model)
                cache.set(key, model.id)
                return model
            return None
        return model.from_id(model_id)

    def count(self, *, key, attribute, filter=None):
        """
        Abstraction function for counting a number of elements. If the
        cache key exists, its value will be returned; otherwise, the
        query will be ran and the resultant count cached and returned.

        :param str key: The cache key to check
        :param attribute: The attribute to count; a model's column
        :param filter: The SQLAlchemy filter expression
        """
        from pulsar import db, cache
        count = cache.get(key)
        if not count:
            query = self._construct_query(db.session.query(func.count(attribute)), filter)
            count = query.first()[0]
            cache.set(key, count)
        return count

    def belongs_to_user(self):
        """
        Function to determine whether or not the model "belongs" to a user
        by comparing against flask.g.user This is meant to be overridden
        by subclasses, and returns False by default (if not overridden).

        :return: ``True`` if "belongs to user", else ``False``
        """
        return False

    def clear_cache(self):
        """Clear the cache key for this instance of a model."""
        from pulsar import cache
        cache.delete(self.cache_key)

    @staticmethod
    def _construct_query(query, filter=None, order=None):
        """
        Convenience function to save code space for query generations.
        Takes filters and orders and applies them to the query if they are present,
        returning a query ready to be ran.

        :param filter: A SQLAlchemy query filter expression
        :param order: A SQLAlchemy query order_by expression

        :return: A Flask-SQLAlchemy ``BaseQuery``
        """
        if filter is not None:
            query = query.filter(filter)
        if order is not None:
            query = query.order_by(order)
        return query
