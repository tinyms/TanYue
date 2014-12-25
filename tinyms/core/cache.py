# -*- coding: utf-8 -*-

__author__ = 'i@tinyms.com'

"""
    werkzeug.contrib.cache
    ~~~~~~~~~~~~~~~~~~~~~~

    The main problem with dynamic Web sites is, well, they're dynamic.  Each
    time a user requests a page, the webserver executes a lot of code, queries
    the database, renders templates until the visitor gets the page he sees.

    This is a lot more expensive than just loading a file from the file system
    and sending it to the visitor.

    For most Web applications, this overhead isn't a big deal but once it
    becomes, you will be glad to have a cache system in place.

    How Caching Works
    =================

    Caching is pretty simple.  Basically you have a cache object lurking around
    somewhere that is connected to a remote cache or the file system or
    something else.  When the request comes in you check if the current page
    is already in the cache and if so, you're returning it from the cache.
    Otherwise you generate the page and put it into the cache. (Or a fragment
    of the page, you don't have to cache the full thing)

    Here is a simple example of how to cache a sidebar for a template::

        def get_sidebar(user):
            identifier = 'sidebar_for/user%d' % user.id
            value = cache.get(identifier)
            if value is not None:
                return value
            value = generate_sidebar_for(user=user)
            cache.set(identifier, value, timeout=60 * 5)
            return value

    Creating a Cache Object
    =======================

    To create a cache object you just import the cache system of your choice
    from the cache module and instantiate it.  Then you can start working
    with that object:

    #>>> from werkzeug.contrib.cache import SimpleCache
    #>>> c = SimpleCache()
    #>>> c.set("foo", "value")
    #>>> c.get("foo")
    #'value'
    #>>> c.get("missing") is None
    True

    Please keep in mind that you have to create the cache and put it somewhere
    you have access to it (either as a module global you can import or you just
    put it into your WSGI application).

    :copyright: (c) 2014 by the Werkzeug Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import os
import re
import errno
import tempfile
from hashlib import md5
from time import time
import pickle as pickle_

iteritems = lambda d, *args, **kwargs: d.iteritems(*args, **kwargs)


def _items(mappingorseq):
    """Wrapper for efficient iteration over mappings represented by dicts
    or sequences::

        >>> for k, v in _items((i, i*i) for i in range(5)):
        ...    assert k*k == v

        >>> for k, v in _items(dict((i, i*i) for i in range(5))):
        ...    assert k*k == v

    """
    if hasattr(mappingorseq, 'items'):
        return iteritems(mappingorseq)
    return mappingorseq


class BaseCache(object):
    """Baseclass for the cache systems.  All the cache systems implement this
    API or a superset of it.

    :param default_timeout: the default timeout (in seconds) that is used if no
                            timeout is specified on :meth:`set`.
    """

    def __init__(self, default_timeout=300):
        self.default_timeout = default_timeout

    def get(self, key):
        """Look up key in the cache and return the value for it.

        :param key: the key to be looked up.
        :returns: The value if it exists and is readable, else ``None``.
        """
        return None

    def delete(self, key):
        """Delete `key` from the cache.

        :param key: the key to delete.
        :returns: Whether the key existed and has been deleted.
        :rtype: boolean
        """
        return True

    def get_many(self, *keys):
        """Returns a list of values for the given keys.
        For each key a item in the list is created::

            foo, bar = cache.get_many("foo", "bar")

        Has the same error handling as :meth:`get`.

        :param keys: The function accepts multiple keys as positional
                     arguments.
        """
        return map(self.get, keys)

    def get_dict(self, *keys):
        """Like :meth:`get_many` but return a dict::

            d = cache.get_dict("foo", "bar")
            foo = d["foo"]
            bar = d["bar"]

        :param keys: The function accepts multiple keys as positional
                     arguments.
        """
        return dict(zip(keys, self.get_many(*keys)))

    def set(self, key, value, timeout=None):
        """Add a new key/value to the cache (overwrites value, if key already
        exists in the cache).

        :param key: the key to set
        :param value: the value for the key
        :param timeout: the cache timeout for the key (if not specified,
                        it uses the default timeout).
        :returns: ``True`` if key has been updated, ``False`` for backend
                  errors. Pickling errors, however, will raise a subclass of
                  ``pickle.PickleError``.
        :rtype: boolean
        """
        return True

    def add(self, key, value, timeout=None):
        """Works like :meth:`set` but does not overwrite the values of already
        existing keys.

        :param key: the key to set
        :param value: the value for the key
        :param timeout: the cache timeout for the key or the default
                        timeout if not specified.
        :returns: Same as :meth:`set`, but also ``False`` for already
                  existing keys.
        :rtype: boolean
        """
        return True

    def set_many(self, mapping, timeout=None):
        """Sets multiple keys and values from a mapping.

        :param mapping: a mapping with the keys/values to set.
        :param timeout: the cache timeout for the key (if not specified,
                        it uses the default timeout).
        :returns: Whether all given keys have been set.
        :rtype: boolean
        """
        rv = True
        for key, value in _items(mapping):
            if not self.set(key, value, timeout):
                rv = False
        return rv

    def delete_many(self, *keys):
        """Deletes multiple keys at once.

        :param keys: The function accepts multiple keys as positional
                     arguments.
        :returns: Whether all given keys have been deleted.
        :rtype: boolean
        """
        return all(self.delete(key) for key in keys)

    def clear(self):
        """Clears the cache.  Keep in mind that not all caches support
        completely clearing the cache.
        :returns: Whether the cache has been cleared.
        :rtype: boolean
        """
        return True

    def inc(self, key, delta=1):
        """Increments the value of a key by `delta`.  If the key does
        not yet exist it is initialized with `delta`.

        For supporting caches this is an atomic operation.

        :param key: the key to increment.
        :param delta: the delta to add.
        :returns: The new value or ``None`` for backend errors.
        """
        value = (self.get(key) or 0) + delta
        return value if self.set(key, value) else None

    def dec(self, key, delta=1):
        """Decrements the value of a key by `delta`.  If the key does
        not yet exist it is initialized with `-delta`.

        For supporting caches this is an atomic operation.

        :param key: the key to increment.
        :param delta: the delta to subtract.
        :returns: The new value or `None` for backend errors.
        """
        value = (self.get(key) or 0) - delta
        return value if self.set(key, value) else None


class NullCache(BaseCache):
    """
        A cache that doesn't cache.  This can be useful for unit testing.
    """


class SimpleCache(BaseCache):
    """Simple memory cache for single process environments.  This class exists
    mainly for the development server and is not 100% thread safe.  It tries
    to use as many atomic operations as possible and no locks for simplicity
    but it could happen under heavy load that keys are added multiple times.

    :param threshold: the maximum number of items the cache stores before
                      it starts deleting some.
    :param default_timeout: the default timeout that is used if no timeout is
                            specified on :meth:`~BaseCache.set`.
    """

    def __init__(self, threshold=500, default_timeout=300):
        BaseCache.__init__(self, default_timeout)
        self._cache = {}
        self.clear = self._cache.clear
        self._threshold = threshold

    def _prune(self):
        if len(self._cache) > self._threshold:
            now = time()
            for idx, (key, (expires, _)) in enumerate(self._cache.items()):
                if expires <= now or idx % 3 == 0:
                    self._cache.pop(key, None)

    def get(self, key):
        try:
            expires, value = self._cache[key]
            if expires > time():
                return pickle_.loads(value)
        except (KeyError, pickle_.PickleError):
            return None

    def set(self, key, value, timeout=None):
        if timeout is None:
            timeout = self.default_timeout
        self._prune()
        self._cache[key] = (time() + timeout, pickle_.dumps(value,
                                                            pickle_.HIGHEST_PROTOCOL))
        return True

    def add(self, key, value, timeout=None):
        if timeout is None:
            timeout = self.default_timeout
        self._prune()
        item = (time() + timeout, pickle_.dumps(value,
                                                pickle_.HIGHEST_PROTOCOL))
        if key in self._cache:
            return False
        self._cache.setdefault(key, item)
        return True

    def delete(self, key):
        return self._cache.pop(key, None) is not None


_test_memcached_key = re.compile(r'[^\x00-\x21\xff]{1,250}$').match


class FileSystemCache(BaseCache):
    """A cache that stores the items on the file system.  This cache depends
    on being the only user of the `cache_dir`.  Make absolutely sure that
    nobody but this cache stores files there or otherwise the cache will
    randomly delete files therein.

    :param cache_dir: the directory where cache files are stored.
    :param threshold: the maximum number of items the cache stores before
                      it starts deleting some.
    :param default_timeout: the default timeout that is used if no timeout is
                            specified on :meth:`~BaseCache.set`.
    :param mode: the file mode wanted for the cache files, default 0600
    """

    #: used for temporary files by the FileSystemCache
    _fs_transaction_suffix = '.__wz_cache'

    def __init__(self, cache_dir, threshold=500, default_timeout=300, mode=0o600):
        BaseCache.__init__(self, default_timeout)
        self._path = cache_dir
        self._threshold = threshold
        self._mode = mode

        try:
            os.makedirs(self._path)
        except OSError as ex:
            if ex.errno != errno.EEXIST:
                raise

    def _list_dir(self):
        """return a list of (fully qualified) cache filenames
        """
        return [os.path.join(self._path, fn) for fn in os.listdir(self._path)
                if not fn.endswith(self._fs_transaction_suffix)]

    def _prune(self):
        entries = self._list_dir()
        if len(entries) > self._threshold:
            now = time()
            try:
                for idx, fname in enumerate(entries):
                    remove = False
                    with open(fname, 'rb') as f:
                        expires = pickle_.load(f)
                    remove = expires <= now or idx % 3 == 0

                    if remove:
                        os.remove(fname)
            except (IOError, OSError):
                pass

    def clear(self):
        for fname in self._list_dir():
            try:
                os.remove(fname)
            except (IOError, OSError):
                return False
        return True

    def _get_filename(self, key):
        if isinstance(key, str):
            # XXX unicode review
            key = key.encode('utf-8')
        hash_ = md5(key).hexdigest()
        return os.path.join(self._path, hash_)

    def get(self, key):
        filename = self._get_filename(key)
        try:
            with open(filename, 'rb') as f:
                if pickle_.load(f) >= time():
                    return pickle_.load(f)
                else:
                    os.remove(filename)
                    return None
        except (IOError, OSError, pickle_.PickleError):
            return None

    def add(self, key, value, timeout=None):
        filename = self._get_filename(key)
        if not os.path.exists(filename):
            return self.set(key, value, timeout)
        return False

    def set(self, key, value, timeout=None):
        if timeout is None:
            timeout = self.default_timeout
        filename = self._get_filename(key)
        self._prune()
        try:
            fd, tmp = tempfile.mkstemp(suffix=self._fs_transaction_suffix,
                                       dir=self._path)
            with os.fdopen(fd, 'wb') as f:
                pickle_.dump(int(time() + timeout), f, 1)
                pickle_.dump(value, f, pickle_.HIGHEST_PROTOCOL)
            os.rename(tmp, filename)
            os.chmod(filename, self._mode)
        except (IOError, OSError):
            return False
        else:
            return True

    def delete(self, key):
        try:
            os.remove(self._get_filename(key))
        except (IOError, OSError):
            return False
        else:
            return True


class CacheFactory():
    DEFAULT_TIMEOUT = 300
    MEM_THRESHOLD = 500
    FILE_THRESHOLD = 1000
    STORAGE_PATH = tempfile.gettempdir()
    __C_MEM__ = None
    __C_FILE__ = None

    def __init__(self):
        pass

    @staticmethod
    def simple():
        if not CacheFactory.__C_MEM__:
            CacheFactory.__C_MEM__ = SimpleCache(threshold=CacheFactory.MEM_THRESHOLD,
                                                 default_timeout=CacheFactory.DEFAULT_TIMEOUT)
        return CacheFactory.__C_MEM__

    @staticmethod
    def file():
        if not CacheFactory.__C_FILE__:
            CacheFactory.__C_FILE__ = FileSystemCache(CacheFactory.STORAGE_PATH,
                                                      threshold=CacheFactory.FILE_THRESHOLD,
                                                      default_timeout=CacheFactory.DEFAULT_TIMEOUT)
        return CacheFactory.__C_FILE__

    @staticmethod
    def cache(cache_storage="mem"):
        if "mem" == cache_storage:
            return CacheFactory.simple()
        return CacheFactory.file()