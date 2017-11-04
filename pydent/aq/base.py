"""Contains the Base class definition"""

import aq

class Base:

    """Base model class from which all models inherit"""

    def __init__(self, name):
        """Make a new Base object"""
        self.name = name

    def record(self, data):
        """Build a new Record from raw data, usually retrieved from a josn request to Aquarium"""
        record_class = eval("aq." + self.name + "Record")
        return record_class(self, data)

    def find(self, id):
        """Find a record with the given id"""
        result = aq.http.post('/json', {"model": self.name, "id": id})
        if "errors" in result:
            raise Exception(self.name + ": " + result["errors"])
        return self.record(result)

    def find_by_name(self, name):
        """Find a record with the given name"""
        result = aq.http.post('/json', {
            "model": self.name,
            "method": "find_by_name",
            "arguments": [name]
        })
        if result == None:
            raise Exception(self.name + " '" + name + "' not found")
        if "errors" in result:
            raise Exception(self.name + ": " + result["errors"])
        return self.record(result)

    def array_query(self, method, args, rest, opts={}):
        """Perform an array query such as all or where"""
        options = {"offset": -1, "limit": -1, "reverse": False}
        options.update(opts)
        query = {"model": self.name,
                 "method": method,
                 "arguments": args,
                 "options": options}
        query.update(rest)
        r = aq.http.post('/json', query)
        if "errors" in r:
            raise Exception(self.name + ": " + r["errors"])
        return [self.record(data) for data in r]

    def all(self, rest={}, opts={}):
        """Retrieve all records for the given model from Aquarium"""
        options = {"offset": -1, "limit": -1, "reverse": False}
        options.update(opts)
        return self.array_query("all", [], rest, options)

    def where(self, criteria, methods={}, opts={}):
        """Perform a where querey"""
        options = {"offset": -1, "limit": -1, "reverse": False}
        options.update(opts)
        return self.array_query("where", criteria, methods, options)
