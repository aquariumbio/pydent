"""Utilities

==========
utils
==========

Submodules
==========

.. autosummary::
    :toctree: _autosummary

    async_requests
    logger

"""
import pprint as pprint_module

from pydent.utils.async_requests import make_async
from .loggable import Loggable
import math

printer = pprint_module.PrettyPrinter(indent=1)
pprint = printer.pprint
pformat = printer.pformat


def filter_list(objlist, **kwargs):
    """Filters a list of objects based on attributes in kwargs."""
    intersection = []
    for obj in objlist:
        is_ok = True
        for k in kwargs:
            if not hasattr(obj, k):
                is_ok = False
                break
            if not getattr(obj, k) == kwargs[k]:
                is_ok = False
                break
        if is_ok:
            intersection.append(obj)
    return type(objlist)(intersection)


def url_build(*parts):
    """Join parts of a url into a string."""
    url = "/".join(p.strip("/") for p in parts)
    return url


def empty_copy(obj):
    """Return an empty copy of an object for copying purposes."""

    class Empty(obj.__class__):
        def __init__(self):
            pass

    newcopy = Empty()
    newcopy.__class__ = obj.__class__
    return newcopy


def condense_long_lists(d, max_list_len=20):
    """Condense the long lists in a dictionary.

    :param d: dictionary to condense
    :type d: dict
    :param max_len: max length of lists to display
    :type max_len: int
    :return:
    :rtype:
    """
    if isinstance(d, dict):
        return_dict = {}
        for k in d:
            return_dict[k] = condense_long_lists(dict(d).pop(k))
        return dict(return_dict)
    elif isinstance(d, list):
        if len(d) > max_list_len:
            g = max_list_len / 2
            return d[: math.floor(g)] + ["..."] + d[-math.ceil(g) :]
        else:
            return d[:]
    return str(d)


def pprint_data(data, width=80, depth=10, max_list_len=20, compact=True, indent=1
                 ):
    return pprint.pformat(
        condense_long_lists(data, max_list_len=max_list_len),
        indent=indent,
        width=width,
        depth=depth,
        compact=compact,
    )
# def filter_dictionary(dictionary, filter_function):
#     new_dict = {}
#     if isinstance(dictionary, dict):
#         for key, val in dictionary.items():
#             if filter_function(key, val):
#                 new_dict[key] = val
#             if isinstance(val, dict):
#                 new_dict[key] = filter_dictionary(val, filter_function)
#         return new_dict

# def ignore_none(d):
#     return filter_dictionary(d, lambda k, v: v is not None)
#
# def ignore_empty(d):
#     return filter_dictionary(d, lambda k, v: v != [])
