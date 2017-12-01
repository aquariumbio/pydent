"""Misc. utilities for pydent"""

from pydent.utils.magiclist import MagicList, magiclist
from marshmallow import pprint


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
