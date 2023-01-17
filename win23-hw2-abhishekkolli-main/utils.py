from __future__ import annotations

from collections.abc import Iterable, Mapping
from sys import getsizeof

from hashtable import HashTable


# A recipe to recursively get the size of an object in memory.
# Adapted from the following blog post:
# https://code.tutsplus.com/tutorials/understand-how-much-memory-your-python-objects-use--cms-25609
def _deep_getsizeof(obj: object, ids_already_counted: set[int]):
    """Find the memory footprint of a Python object.

    The sys.getsizeof function is shallow.
    It counts each object inside a container as pointer only regardless of how big it really is.

    This is a recursive sizeof function that traverses the object graph, supporting containers
    such as a dictionary holding nested dictionaries with lists of lists and tuples and sets.

    Parameters
    ----------
    obj : object
        The object to analyze.
    ids_already_counted : set[int]
        Memory addresses of objects which have already been counted.

    Returns
    -------
    size : int
        Memory size of the object, in bytes.
    """
    if id(obj) in ids_already_counted:
        return 0

    d = _deep_getsizeof

    r = getsizeof(obj)
    ids_already_counted.add(id(obj))

    if isinstance(obj, str) or isinstance(0, str):
        return r

    # Special case for HashTable ensures that the tuple objects in nonempty buckets are counted.
    if isinstance(obj, HashTable):
        return r + sum(d(x, ids_already_counted) for x in obj.items())

    if isinstance(obj, Mapping):
        return r + sum(
            d(k, ids_already_counted) + d(v, ids_already_counted) for k, v in obj.items()
        )  # Changed

    if isinstance(obj, Iterable):
        return r + sum(d(x, ids_already_counted) for x in obj)

    return r


# Expose a wrapper function which creates the ids_already_counted set automatically
def deep_getsizeof(obj: object):
    return _deep_getsizeof(obj, set())
