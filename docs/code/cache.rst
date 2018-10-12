Cache
======

Site load is no joke, and in order to keep the tracker running smoothly a lot of data 
gets cached with Redis. Instead of fetching data from the database, we can fetch data 
from RAM and only fetch new data from the database when it changes. In pulsar, caching is 
heavily abstracted--the majority of cache work is done behind the scenes in the model 
mixins and cache module.

Models subclassing the ``SinglePKMixin`` will be cached whenever they are fetched from 
the database. Future requests that request that resource will access the cached model 
instead of querying the database. Caching can result in out of date data, but steps are 
taken against that happening in core. Whenever a model is modified and flushed to the 
database, a listener (``clear_cache_dirty``) will automatically expire its cache key. The 
only keys which need to be explicitly expired in a view or model are the cache keys for 
lists of models, which are typically lists of their primary keys.

Below is the cache class--it contains the interface used to communicate with redis. Below 
it is the listener that automatically clears cache keys upon database flush.

.. automodule:: core.cache
    :members:
    :undoc-members:
    :show-inheritance:
