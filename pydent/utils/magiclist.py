"""
Utilities
"""

from functools import wraps

class MagicList(list):
    """List-like class that collects attributes and applies functions
    but acts like a list in every other regard.

    .. code-block:: python

        ml = MagicList(["string1   ", "   string2"])
        m1.strip().upper()
        #=> ["STRING1", "STRING2"]

    """

    def apply(self, fxn):
        return MagicList([fxn(x) for x in self])

    def __getitem__(self, key):
        if isinstance(key, slice):
            return MagicList(super().__getitem__(key))
        return super().__getitem__(key)

    def __getattr__(self, item):
        return MagicList([getattr(x, item) for x in self])

    def call(self, *args, **kwargs):
        return MagicList([x(*args, **kwargs) for x in self])

    def __call__(self, *args, **kwargs):
        return MagicList([x(*args, **kwargs) for x in self])


def magiclist(fxn):
    """Decorator that turns a returned value from a list to a MagicList (if possible). Otherwise
    returns original value"""
    @wraps(fxn)
    def magiclist_wrapper(*args, **kwargs):
        ret = fxn(*args, **kwargs)
        try:
            iter(ret)
            ret = MagicList(ret)
        except TypeError:
            pass
        return ret

    return magiclist_wrapper
