from typing import Any, Dict, List, Optional, Type, TypeVar, Union

import flask
from flask_sqlalchemy import BaseQuery, Model
from sqlalchemy import func
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.orm.session import make_transient_to_detached
from sqlalchemy.sql.elements import BinaryExpression

from pulsar import APIException, _404Exception, _403Exception, cache, db

MDL = TypeVar('MDL', bound='ModelMixin')


class ModelMixin(Model):
    """
    This is a custom model mixin for the pulsar project, which adds caching
    and JSON serialization functionality to the base model. Subclasses are
    expected to define their serializable attributes, permission restrictions,
    and cache key template with the following class attributes. They are required
    if one wants to cache or serialize data for a model. By default, all "serialize"
    tuples are empty, so only the populated ones need to be defined.

    * ``__cache_key__`` (``str``)
    * ``__serialize__`` (``tuple``)
    * ``__serialize_self__`` (``tuple``)
    * ``__serialize_detailed__`` (``tuple``)
    * ``__serialize_very_detailed__`` (``tuple``)
    * ``__serialize_nested_include__`` (``tuple``)
    * ``__serialize_nested_exclude__`` (``tuple``)
    * ``__permission_detailed__`` (``str``)
    * ``__permission_very_detailed__`` (``str``)

    When a model is serialized in an API response, the permissions assigned to a user
    and the permissions listed in the above attributes will determine which properties
    of the model are returned. Attributes in ``__serialize__`` are viewable to anyone
    with permission to access the resource, attributes in ``__serialize_self__`` are
    viewable by anyone who passes the ``belongs_to_user`` function. Attributes in
    ``__serialize_detailed__`` and ``__serialize_very_detailed__`` are viewable by users
    with the permissions defined in ``__permission_detailed__`` and
    ``__permission_very_detailed__``, respectively.

    Other models or values built off from column values can be serialized into JSON by
    taking advantage of the @property decorator. Property names can be included in the
    serialization tuples, and their functions can return (multiple) other models.

    Nested model properties will also be serialized if they are the value of a ``dict``
    or in a ``list``. When nested models are serialized, all attributes listed in
    ``__serialize_nested_exclude__`` will be excluded, while all attributes in
    ``__serialize_nested_include__`` will be included. For example, when embedding a user
    in the forum post JSON response, the nested list of APIKey models can be excluded.

    Due to how models are cached, writing out the logic to obtain from cache and,
    if the cache call returned nothing, execute a query for every model is tedious
    and repetitive. Generalized functions to abstract those are included in this class,
    and are expected to be utilized wherever possible.

    Some of those functions may need to be overridden by the subclass. The base cache
    key property and ``from_id`` classmethod assume that an ``id`` property exists and
    that the cache key only accepts an ID kwarg.

    It's not a true mixin in that it's monolithic and inherits from the base class,
    but let's pretend it is so our type analysis works.
    """

    __cache_key__: str = None
    __deletion_attr__: str = None

    __serialize__: tuple = ()
    __serialize_self__: tuple = ()
    __serialize_detailed__: tuple = ()
    __serialize_very_detailed__: tuple = ()
    __serialize_nested_include__: tuple = ()
    __serialize_nested_exclude__: tuple = ()

    __permission_detailed__: Optional[str] = None
    __permission_very_detailed__: Optional[str] = None

    @property
    def cache_key(self) -> str:
        """
        Default property for cache key which should be overridden if the
        cache key is not formatted with an ID column. If the cache key
        string for the model only takes an {id} param, then this function
        will suffice.

        :return:           The cache key of the model
        :raises NameError: If the model does not have a cache key
        """
        return self.create_cache_key(id=self.id)

    @classmethod
    def from_id(cls: Type[MDL],
                id: Union[str, int, None],
                *,
                include_dead: bool = False,
                _404: bool = False,
                asrt: str = None) -> Optional[MDL]:  # FIXME
        """
        Default classmethod constructor to get an object by its PK ID.
        If the object has a deleted/revoked/expired column, it will compare a
        ``include_dead`` kwarg against it. This function first attempts to load
        an object from the cache by formatting its ``__cache_key__`` with the
        ID parameter, and executes a query if the object isn't cached.
        Can optionally raise a ``_404Exception`` if the object is not queried.

        :param id:             The primary key ID of the object to query for
        :param include_dead:   Whether or not to return deleted/revoked/expired objects
        :param _404:           Whether or not to raise a _404Exception with the value of
                               _404 and the class name as the resource name if a model is not found
        :param asrt:           Whether or not to check for ownership of the model or a permission.
                               Can be a boolean to purely check for ownership, or a permission
                               string which can override ownership and access the model anyways.

        :return:               The object corresponding to the given ID, if it exists
        :raises _404Exception: If ``_404`` is passed and a model is not found or accessible
        """
        if id:
            model = cls.from_cache(
                key=cls.create_cache_key(id=id),
                query=cls.query.filter(cls.id == id))
            if (model is not None
                    and model.can_access(asrt, error=not _404)
                    and (include_dead
                         or not cls.__deletion_attr__
                         or not getattr(model, cls.__deletion_attr__, False))):
                return model
        if _404:
            raise _404Exception(f'{cls.__name__} {id}')
        return None

    @classmethod
    def from_cache(cls: Type[MDL],
                   key: str,
                   *,
                   query: BaseQuery = None) -> Optional[MDL]:
        """
        Check the cache for an instance of this model and attempt to load
        its attributes from the cache instead of from the database.
        If found, the object is merged into the database session and returned.
        Otherwise, if a query is passed, the query is ran and the result is cached and
        returned. Model returns ``None`` if the object doesn't exist.

        :param key:   The cache key to get
        :param query: The SQLAlchemy query

        :return:      An instance of this class, if the cache key or query produced results
        """
        data = cache.get(key)
        obj = cls._create_obj_from_cache(data)
        if obj:
            return obj
        else:
            cache.delete(key)
        if query:
            obj = query.first()
            cache.cache_model(obj)
            return obj
        return None

    @classmethod
    def _create_obj_from_cache(cls: Type[MDL],
                               data: Any) -> Optional[MDL]:
        if cls._valid_data(data):
            obj = cls(**data)
            make_transient_to_detached(obj)
            obj = db.session.merge(obj, load=False)
            return obj
        return None

    @classmethod
    def from_query(cls: Type[MDL],
                   *,
                   key: str,
                   filter: BinaryExpression = None,
                   order: BinaryExpression = None) -> Optional[MDL]:
        """
        Function to get a single object from the database (via ``limit(1)``, ``query.first()``).
        Getting the object via the provided cache key will be attempted first; if
        it does not exist, then a query will be constructed with the other
        parameters. The resultant object (if exists) will be cached and returned.

        **The queried model must have a primary key column named ``id`` and a
        ``from_id`` classmethod constructor.**

        :param key:    The cache key belonging to the object
        :param filter: A SQLAlchemy expression to filter the query with
        :param order:  A SQLAlchemy expression to order the query by

        :return:       The queried model, if it exists
        """
        cls_id = cache.get(key)
        if not cls_id or not isinstance(cls_id, int):
            query = cls._construct_query(cls.query, filter, order)
            model = query.limit(1).first()
            if model:
                if not cache.has(model.cache_key):
                    cache.cache_model(model)
                cache.set(key, model.id)
                return model
            return None
        return cls.from_id(cls_id)

    @classmethod
    def get_many(cls: Type[MDL],
                 *,
                 key: str,
                 filter: BinaryExpression = None,
                 order: BinaryExpression = None,
                 required_properties: tuple = (),
                 include_dead: bool = False,
                 asrt: str = None,
                 page: int = None,
                 limit: int = 50,
                 reverse: bool = False,
                 expr_override: BinaryExpression = None) -> List[MDL]:
        """
        An abstracted function to get a list of IDs from the cache with a cache key,
        and query for those IDs if the key does not exist. If the query needs to be ran,
        a list will be created from the first element in every returned tuple result, like so:
        ``[x[0] for x in cls.query.all()]``

        That list will be converted into models, using passed keyword arguments to modify
        which elements are included and which aren't. Pagination occurs here, although it is
        optional and ignored if neither page nor limit is set.

        :param key:                 The cache key to check (and return if present)
        :param filter:              A SQLAlchemy filter expression to be applied to the query
        :param order:               A SQLAlchemy order_by expression to be applied to the query
        :param required_properties: Properties required to validate to ``True``. This can break
                                    pagination (varying # on one page)
                                    for a retrieved item to be included in the returned list
        :param include_dead:        Whether or not to include deleted/revoked/expired models
        :param asrt:                Whether or not to check for ownership of the model or a
                                    permission. Can be a boolean to purely check for ownership,
                                    or a permission string which can override ownership and
                                    access the model anyways.
        :param page:                The page number of results to return
        :param limit:               The limit of results to return, defaults to 50 if page
                                    is set, otherwise infinite
        :param reverse:             Whether or not to reverse the order of the list
        :param expr_override:       If passed, this will override filter and order, and be
                                    called verbatim in a ``db.session.execute`` if the cache
                                    key does not exist

        :return:                    A list of objects matching the query specifications
        """
        # TODO: Profile efficiency of this function with a bunch of random data
        ids = cls.get_ids_of_many(key, filter, order, include_dead, expr_override)
        if reverse:
            ids.reverse()
        if page is not None:
            all_next_ids = ids[(page - 1) * limit:]
            ids, extra_ids = all_next_ids[:limit], all_next_ids[limit:]

        models: Dict[Union[int, str], MDL] = {}
        while len(models) < limit:
            uncached_ids = []
            cached_dict = cache.get_dict(*(cls.create_cache_key(id=i) for i in ids))
            for i, (k, v) in zip(ids, cached_dict.items()):
                if v:
                    models[i] = cls._create_obj_from_cache(v)
                else:
                    uncached_ids.append(i)

            qry_models = cls._construct_query(cls.query, filter).filter(
                cls.id.in_(uncached_ids)).all()
            cache.cache_models(qry_models)
            for model in qry_models:
                models[model.id] = model
            if required_properties:
                models = {k: m for k, m in models.items() if all(
                    getattr(m, rp, False) for rp in required_properties)}
            if asrt:
                models = {k: m for k, m in models.items() if m.can_access(asrt)}
            if not page or not extra_ids:
                break
            ids = extra_ids[:abs(limit - len(models))]
            extra_ids = extra_ids[abs(limit - len(models)):]
        return list(models.values())

    @classmethod
    def get_ids_of_many(cls,
                        key: str,
                        filter: BinaryExpression = None,
                        order: BinaryExpression = None,
                        include_dead: bool = False,
                        expr_override: BinaryExpression = None) -> List[Union[int, str]]:
        """
        Get a list of object IDs meeting query criteria. Fetching from the
        cache with the provided cache key will be attempted first; if the cache
        key does not exist then a query will be ran. Calls with ``include_dead=True`` are
        saved under a different cache key. ``include_dead`` does not affect the query results
        when passing ``expr_override``.

        :param key:                 The cache key to check (and return if present)
        :param filter:              A SQLAlchemy filter expression to be applied to the query
        :param order:               A SQLAlchemy order_by expression to be applied to the query
        :param include_dead:        Whether or not to include dead results in the IDs list
        :param expr_override:       If passed, this will override filter and order, and be
                                    called verbatim in a ``db.session.execute`` if the cache
                                    key does not exist

        :return:                    A list of IDs
        """
        key = f'{key}_incl_dead' if include_dead else key
        ids = cache.get(key)
        if not ids or not isinstance(ids, list):
            if expr_override is not None:
                ids = [x[0] for x in db.session.execute(expr_override)]
            else:
                query = cls._construct_query(db.session.query(cls.id), filter, order)
                if not include_dead and cls.__deletion_attr__:
                    query = query.filter(getattr(cls, cls.__deletion_attr__) == 'f')
                ids = [x[0] for x in query.all()]
            cache.set(key, ids)
        return ids

    @classmethod
    def is_valid(cls,
                 id: Union[int, str, None],
                 error: bool = False) -> bool:
        """
        Check whether or not the object exists and isn't deleted.

        :param id:            The object ID to validate
        :param error:         Whether or not to raise an APIException on validation fail
        :return:              Validity of the object
        :raises APIException: If error param is passed and ID is not valid
        """
        obj = cls.from_id(id)
        valid = (obj is not None and (
            cls.__deletion_attr__ is None
            or not getattr(obj, cls.__deletion_attr__, False)))
        if error and not valid:
            raise APIException(f'Invalid {cls.__name__} ID.')
        return valid

    @classmethod
    def create_cache_key(cls, **kwargs: Union[int, str]) -> str:
        """
        Populate the ``__cache_key__`` class attribute with the kwargs.

        :param kwargs:     The keywords that will be fed into the ``str.format`` function

        :return:           The cache key
        :raises NameError: If the cache key is undefined or improperly defined
        """
        if cls.__cache_key__:
            try:
                return cls.__cache_key__.format(**kwargs)
            except KeyError:
                pass
        raise NameError('The cache key is undefined or improperly defined in this model.')

    @classmethod
    def update_many(cls, *,
                    ids: List[Union[str, int]],
                    update: Dict[str, Any],
                    sychronize_session: bool = False) -> None:
        """
        Construct and execute a query affecting all objects with IDs in the
        list of IDs passed to this function. This is only meant to be used for
        models with an ID primary key and cache key formatted by ID.

        :param ids:                 The list of primary key IDs to update
        :param update:              The dictionary of column values to update
        :param synchronize_session: Whether or not to update the session after
                                    the query; should be True if the objects are
                                    going to be used after updating
        """
        if ids:
            db.session.query(cls).filter(cls.id.in_(ids)).update(
                update, synchronize_session=sychronize_session)
            db.session.commit()
            cache.delete_many(*(cls.create_cache_key(id=id) for id in ids))

    @classmethod
    def _new(cls: Type[MDL],
             **kwargs: Any) -> MDL:
        """
        Create a new instance of the model, add it to the instance, cache it, and return it.

        :param kwargs: The new attributes of the model
        """
        model = cls(**kwargs)
        db.session.add(model)
        db.session.commit()
        cache.cache_model(model)
        return model

    @classmethod
    def _valid_data(cls, data: dict) -> bool:
        """
        Validate the data returned from the cache by ensuring that it is a dictionary
        and that the returned values match the columns of the object.

        :param data: The stored object data from the cache to validate
        :return:     Whether or not the data is valid
        """
        return (bool(data)
                and isinstance(data, dict)
                and set(data.keys()) == set(cls.__table__.columns.keys()))

    def count(self,
              *,
              key: str,
              attribute: InstrumentedAttribute,
              filter: BinaryExpression = None) -> int:
        """
        An abstracted function for counting a number of elements matching a query. If the
        passed cache key exists, its value will be returned; otherwise, the passed query
        will be ran and the resultant count cached and returned.

        :param key:       The cache key to check
        :param attribute: The attribute to count; a model's column
        :param filter:    The SQLAlchemy filter expression

        :return: The number of rows matching the query element
        """
        count = cache.get(key)
        if not isinstance(count, int):
            query = self._construct_query(db.session.query(func.count(attribute)), filter)
            count = query.first()[0]
            cache.set(key, count)
        return count

    def can_access(self,
                   permission: str = None,
                   error: bool = False) -> bool:
        """
        Determines whether or not the requesting user can access the following resource.
        If no permission is specified, any user can access the resource. If a permission is
        specified, then access is restricted to users with that permission or "ownership"
        of this object. Ownership is determined with the ``belongs_to_user`` method.

        :param permission: Permission to restrict access to
        :return:           Whether or not the requesting user can access the resource
        """
        access = (permission is None
                  or self.belongs_to_user()
                  or flask.g.user.has_permission(permission))
        if error and not access:
            raise _403Exception
        return access

    def belongs_to_user(self) -> bool:
        """
        Function to determine whether or not the model "belongs" to a user by comparing
        against flask.g.user This is meant to be overridden by subclasses, although, by default,
        if the model has a ``user_id`` column, it compares ``flask.g.user`` with that column.
        If that column does not exist, ``False`` will be returned by default.

        :return: Whether or not the object "belongs" to the user
        """
        return flask.g.user is not None and flask.g.user.id == getattr(self, 'user_id', False)

    def del_property_cache(self, prop: str) -> None:
        """
        Delete a property from the property cache.

        :param prop: The property to delete
        """
        try:
            del self._property_cache[prop]
        except (AttributeError, KeyError):
            pass

    @staticmethod
    def _construct_query(query: BaseQuery,
                         filter: BinaryExpression = None,
                         order: BinaryExpression = None) -> BaseQuery:
        """
        A convenience function to save code space for query generations. Takes filters
        and order_bys and applies them to the query, returning a query ready to be ran.

        :param query:  A query that can be built upon
        :param filter: A SQLAlchemy query filter expression
        :param order:  A SQLAlchemy query order_by expression

        :return:       A Flask-SQLAlchemy ``BaseQuery``
        """
        if filter is not None:
            query = query.filter(filter)
        if order is not None:
            query = query.order_by(order)
        return query
