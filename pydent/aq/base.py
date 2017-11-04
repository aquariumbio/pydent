import aq


class Base:

    def __init__(self, name):
        self.name = name

    def record(self, data):
        record_class = eval("aq." + self.name + "Record")
        return record_class(self, data)

    def find(self, id):
        result = aq.http.post('/json', {"model": self.name, "id": id})
        if "errors" in result:
            raise Exception(self.name + ": " + result["errors"])
        return self.record(result)

    def find_by_name(self, name):
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
        options = {"offset": -1, "limit": -1, "reverse": False}
        options.update(opts)
        return self.array_query("all", [], rest, options)

    def where(self, criteria, methods={}, opts={}):
        options = {"offset": -1, "limit": -1, "reverse": False}
        options.update(opts)
        return self.array_query("where", criteria, methods, options)