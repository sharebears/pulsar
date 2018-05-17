from typing import Any, Optional, Union

import flask
from flask_sqlalchemy import SignallingSession
from redis import Redis  # noqa
from werkzeug.contrib.cache import RedisCache

from pulsar.base_model import BaseModel


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
            timeout: Optional[int] = None) -> Optional[int]:
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
        if value:
            flask.g.cache_keys['get'].add(key)
        return value

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
        if result:
            flask.g.cache_keys['set'].add(key)
        return result

    def delete(self, key: str) -> bool:
        """
        Delete key from the cache.

        :param key: The key to delete
        :return:    Whether or not the key existed and has been deleted
        """
        key = key.lower()
        result = super().delete(key)
        if result:
            flask.g.cache_keys['delete'].add(key)
        return result

    def ttl(self, key: str) -> int:
        """
        Return the time to live (time until expiry) for a cache key.

        :param key: The cache key to check for expiry
        :return:    The seconds left until a key expires
        """
        value = self._client.ttl((self.key_prefix + key).lower())
        if value:
            flask.g.cache_keys['ttl'].add(key)
        return value

    def cache_model(self,
                    model: BaseModel,
                    timeout: int = None) -> Union[str, None]:
        """
        Cache a SQLAlchemy model. Does nothing when ``model`` is ``None``.

        :param model:   The model we want to cache
        :param timeout: The number of seconds to persist the cached value for

        :return: The cache key of the model
        """
        if model and isinstance(model, BaseModel):
            data = {}
            for attr in model.__table__.columns.keys():
                data[attr] = getattr(model, attr, None)
            self.set(model.cache_key, data, timeout or self.default_timeout)
            return model.cache_key
        return None


def clear_cache_dirty(session: SignallingSession) -> None:
    """
    Clear the cache key of every dirty/deleted object before DB commit.

    :param session: The database session about to be committed
    """
    from pulsar import cache
    for obj in session.dirty.union(session.deleted):
        if obj.__cache_key__:
            cache.delete(obj.cache_key)
