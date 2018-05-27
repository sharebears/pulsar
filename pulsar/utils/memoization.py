from functools import wraps
from typing import Callable


def cached_property(func: Callable) -> property:
    @wraps(func)
    def wrapper(self):
        try:
            return self._property_cache[func.__name__]
        except AttributeError:
            self._property_cache = {}
            rv = self._property_cache[func.__name__] = func(self)
        except KeyError:
            rv = self._property_cache[func.__name__] = func(self)
        return rv
    return property(wrapper)
