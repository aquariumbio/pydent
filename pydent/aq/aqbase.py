from pillowtalk import *
from .aqhttp import AqHTTP

class AqBase(PillowtalkBase):
    """ Basic model for api items """

    @classmethod
    def post_json(cls, data):
        d = {'model': cls.__name__}
        d.update(data)
        r = AqHTTP.session.post('json', json=d)
        m = cls.load(r)
        if type(m) is list:
            for result, model in zip(r, m):
                model.raw = result
        else:
            m.raw = r
        return m

    @classmethod
    def find(cls, id):
        return cls.post_json({"id": id})

    @classmethod
    def find_by_name(cls, name):
        return cls.post_json({"method": "find_by_name", "arguments": [name]})

    @classmethod
    def array_query(cls, method, args, rest, opts={}):
        options = {"offset": -1, "limit": -1, "reverse": False}
        options.update(opts)
        query = {"model"    : cls.__name__,
                 "method"   : method,
                 "arguments": args,
                 "options"  : options}
        query.update(rest)
        r = cls.post_json(query)
        if "errors" in r:
            raise Exception(cls.__name__+": "+r["errors"])
        return r

    @classmethod
    def all(cls, rest={}, opts={}):
        options = {"offset": -1, "limit": -1, "reverse": False}
        options.update(opts)
        return cls.array_query("all", [], rest, options)

    @classmethod
    def where(cls, criteria, methods={}, opts={}):
        options = {"offset": -1, "limit": -1, "reverse": False}
        options.update(opts)
        return cls.array_query("where", criteria, methods, options)

    def __eq__(self, other):
        try:
            return self.__dict__ == other.__dict__
        except:
            return False
