from werkzeug.contrib.cache import RedisCache


class Cache(RedisCache):
    """
    A custom implementation of werkzeug's RedisCache.
    This modifies and adds a few functions to RedisCache.
    """

    def inc(self, key, delta=1, timeout=None):
        """
        Increment a cache key if it exists, otherwise create it
        and optionally set a timeout.
        """
        value = super().inc(key, delta)
        if timeout and value == delta:
            self._client.expire(self.key_prefix + key, timeout)
        return value

    def ttl(self, key):
        """Return the time to live (time until expiry) for a cache key."""
        return self._client.ttl(self.key_prefix + key)
