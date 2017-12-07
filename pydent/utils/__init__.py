"""Misc. utilities for pydent"""

from pydent.utils.magiclist import MagicList, magiclist
from inflection import underscore
import pprint


printer = pprint.PrettyPrinter(indent=1)
pprint = printer.pprint
pformat = printer.pformat


def filter_list(objlist, **kwargs):
    intersection = []
    for o in objlist:
        ok = True
        for k in kwargs:
            if not hasattr(o, k):
                ok = False
                break
            if not getattr(o, k) == kwargs[k]:
                ok = False
                break
        if ok:
            intersection.append(o)
    return type(objlist)(intersection)

# def filter_dictionary(dictionary, filter_function):
#     new_dict = {}
#     if isinstance(dictionary, dict):
#         for key, val in dictionary.items():
#             if filter_function(key, val):
#                 new_dict[key] = val
#             if isinstance(val, dict):
#                 new_dict[key] = filter_dictionary(val, filter_function)
#         return new_dict

def ignore_none(d):
    return filter_dictionary(d, lambda k, v: v is not None)

def ignore_empty(d):
    return filter_dictionary(d, lambda k, v: v != [])
