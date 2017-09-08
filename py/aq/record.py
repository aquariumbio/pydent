import aq
import re

class Record:

    def __init__(self,model,data):
        self.model = model
        self.__data = data
        self.__has_one = {}
        self.__has_many = {}
        for key in data:
            setattr(self,key,data[key])

    def has_one(self,name,model,opts={}):
        self.__has_one[name] = { "model": model }
        self.__has_one[name].update(opts)
        if name in self.__data:
            setattr(self,name,model.record(self.__data[name]))

    def get_one(self,name):
        reference = name + "_id"
        result = self.__has_one[name]["model"].find(getattr(self,reference))
        setattr(self,name,result)
        return result

    def snake(self,name):
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    def has_many(self,name,model,opts={}):
        self.__has_many[name] = { "model": model }
        self.__has_many[name].update(opts)
        if name in self.__data:
            records = [ model.record(r) for r in self.__data[name] ]
            setattr(self,name,records)

    def get_many(self,name):
        reference = self.snake(self.model.name) + "_id"
        results = self.__has_many[name]["model"].where({reference: self.id})
        return results

    def __getattr__(self, name):

        # print("method missing for " + name)

        def __get_one_wrapper(name):
            return self.get_one(name)

        def __get_many_wrapper(name):
            return self.get_many(name)

        if name in self.__has_one:
            return __get_one_wrapper(name)
        elif name in self.__has_many:
            return __get_many_wrapper(name)
        else:
            raise Exception("Association " + name + " not found.")
