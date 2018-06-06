from typing import Any, Dict, List, Optional, Union

import flask
from flask_sqlalchemy import SignallingSession
from redis import Redis
from werkzeug.contrib.cache import RedisCache


class Cache(RedisCache):
    """
    A custom implementation of werkzeug's RedisCache.  This modifies and adds
    a few functions to RedisCache. All keys are automatically lowercased. Cache
    key get/set/inc/del accesses are logged in a global variable for debugging
    purposes.
    """
    _client: Redis

    def __init__(self) -> None:
        # Override the RedisCache params we don't need.
        pass

    def init_app(self, app: flask.Flask) -> None:
        # Required flask extension method.
        super().__init__(**app.config['REDIS_PARAMS'])

    def inc(self,
            key: str,
            delta: int = 1,
            timeout: int = None) -> Optional[int]:
        """
        Increment a cache key if it exists, otherwise create it
        and optionally set a timeout.

        :param key:     The cache key to increment
        :param delta:   How much to increment the cache key by
        :param timeout: If the cache key is created in this request, it will be
                        persisted for this many seconds

        :return: The new value of the key, or ``None`` in the event of a
            backend error
        """
        key = key.lower()
        value = super().inc(key, delta)
        if timeout and value == delta:
            self._client.expire(self.key_prefix + key, timeout)
        flask.g.cache_keys['inc'].add(key)
        return value

    def get(self, key: str) -> Any:
        """
        Look up the key in the cache and return the value for it.

        :param key: The key to be looked up
        :returns:   The value if it exists and is readable, else ``None``
        """
        key = key.lower()
        value = super().get(key)
        if value is not None:  # pragma: no cover
            flask.g.cache_keys['get'].add(key)
        return value

    def get_dict(self, *keys: str) -> Optional[dict]:
        """
        Look up multiple keys in the cache and return their values for it.

        :param keys: The keys to be looked up
        :returns:    The values if they exist and are readable, else ``None``
        """
        lower_keys = [key.lower() for key in keys]
        if not lower_keys:
            return {}
        values = super().get_dict(*lower_keys)
        if values is not None:  # pragma: no cover
            flask.g.cache_keys['get_dict'] |= set(lower_keys)
        return values

    def has(self, key: str) -> bool:
        """
        Look up the key in the cache and return whether or not it exists.

        :param key: The key to be looked up
        :returns:   The value if it exists and is readable, else ``None``
        """
        key = key.lower()
        flask.g.cache_keys['has'].add(key)
        return super().has(key)

    def set(self,
            key: str,
            value: Union[int, str, list, dict],
            timeout: int = None) -> bool:
        """
        Add a new key/value to the cache (overwrites value,
        if key already exists in the cache).

        :param key:     The key to set
        :param value:   The value for the key
        :param timeout: The cache timeout for the key in seconds
                        (if not specified, it uses the default timeout).
                        A timeout of 0 indicates that the cache never expires.

        :return:        True if key has been updated, ``False`` for backend
                        errors. Pickling errors, however, will raise a subclass of
                        pickle.PickleError.
        """
        key = key.lower()
        result = super().set(key, value, timeout)
        if result:  # pragma: no cover
            flask.g.cache_keys['set'].add(key)
        return result

    def set_many(self,
                 mapping: Dict[str, Any],
                 timeout: int = None) -> bool:
        """
        Add multiple new key/value pairs to the cache (overwrites value,
        if key already exists in the cache).

        :param mapping: The key/value pairs to set
        :param timeout: The cache timeout for the key in seconds
                        (if not specified, it uses the default timeout).
                        A timeout of 0 indicates that the cache never expires.

        :return:        True if all the keys have been updated, ``False`` for errors
        """
        lower_mapping = {key.lower(): value for key, value in mapping.items()}
        result = super().set_many(lower_mapping, timeout)
        if result:  # pragma: no cover
            flask.g.cache_keys['set_many'] |= set(lower_mapping.keys())
        return result

    def delete(self, key: str) -> bool:
        """
        Delete key from the cache.

        :param key: The key to delete
        :return:    Whether or not the key existed and has been deleted
        """
        key = key.lower()
        result = super().delete(key)
        if result:  # pragma: no cover
            flask.g.cache_keys['delete'].add(key)
        return result

    def delete_many(self, *keys: str) -> bool:
        """
        Delete multiple keys from the cache.

        :param keys: The keys to delete
        :return:     Whether or not all keys have been deleted
        """
        lower_keys = [key.lower() for key in keys]
        result = super().delete_many(*lower_keys)
        flask.g.cache_keys['delete_many'] |= set(lower_keys)
        return result

    def ttl(self, key: str) -> int:
        """
        Return the time to live (time until expiry) for a cache key.

        :param key: The cache key to check for expiry
        :return:    The seconds left until a key expires
        """
        value = self._client.ttl((self.key_prefix + key).lower())
        if value is not None:  # pragma: no cover
            flask.g.cache_keys['ttl'].add(key)
        return value

    def cache_model(self,
                    model,  # TODO: Fix SinglePKMixin circular import.
                    timeout: int = None) -> Optional[str]:
        """
        Cache a SQLAlchemy model. Does nothing when ``model`` is ``None``.

        :param model:   The model we want to cache
        :param timeout: The number of seconds to persist the cached value for

        :return: The cache key of the model
        """
        if model:
            data = {}
            try:
                for attr in model.__table__.columns.keys():
                    data[attr] = getattr(model, attr)
            except AttributeError:  # pragma: no cover
                # TODO: Log this
                return None
            self.set(model.cache_key, data, timeout)
            return model.cache_key
        return None

    def cache_models(self,
                     models: list,  # TODO: Fix SinglePKMixin circular import.
                     timeout: int = None) -> None:
        """
        Cache a SQLAlchemy model. Does nothing when ``model`` is ``None``.

        :param model:   The model we want to cache
        :param timeout: The number of seconds to persist the cached value for

        :return: The cache key of the model
        """
        to_cache = {}
        for model in models:
            data = {}
            try:
                for attr in model.__table__.columns.keys():
                    data[attr] = getattr(model, attr)
            except AttributeError:  # pragma: no cover
                continue  # TODO: Log this
            to_cache[model.cache_key] = data
        self.set_many(to_cache, timeout)


cache = Cache()


def clear_cache_dirty(session: SignallingSession, _, __) -> None:
    """
    Clear the cache key of every dirty/deleted object before DB flush.

    :param session: The database session about to be committed
    """
    for obj in session.dirty.union(session.deleted):
        if getattr(obj, '__cache_key__', None):
            cache.delete(obj.cache_key)
