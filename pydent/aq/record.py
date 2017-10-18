import re
from .utils import utils

_next_rid = 0;

def new_rid():
    global _next_rid
    _next_rid += 1
    return _next_rid

class RecordHook(type):

    records = {}

    def __init__(cls, name, bases, clsdict):
        RecordHook.add_record(cls)
        super(RecordHook, cls).__init__(name, bases, clsdict)

    @staticmethod
    def add_record(record_class):
        t = RecordHook.records
        RecordHook.records[record_class.__name__] = record_class

            # def __getattr__(cls, item):
    #     sessions = cls.sessions
    #     if item in sessions:
    #         cls.set(item)
    #     else:
    #         return getattr(cls, item)

class Record(object, metaclass=RecordHook):

    def __init__(self,model,data):
        self.model = model
        self.id = None
        self.__data = data
        self.__has_one = {}
        self.__has_many = {}
        self.__has_many_generic = {}
        self._rid = None
        for key in data:
            setattr(self,key,data[key])

    @property
    def rid(self):
        if not self._rid:
            self._rid = new_rid()
        return self._rid

    def has_one(self,name,model,opts={}):
        self.__has_one[name] = { "model": model }
        self.__has_one[name].update(opts)
        if name in self.__data:
            setattr(self,name,model.record(self.__data[name]))
            # also delete attr name = "_id" if it exists

    def get_one(self,name):
        if "reference" in self.__has_one[name]:
            reference = self.__has_one[name]["reference"]
        else:
            reference = name + "_id"
        fid = getattr(self,reference)
        if fid:
            result = self.__has_one[name]["model"].find(fid)
        else:
            result = None
        setattr(self,name,result)
        return result

    def has_many(self,name,model,opts={}):
        self.__has_many[name] = { "model": model }
        self.__has_many[name].update(opts)
        if name in self.__data:
            records = [ model.record(r) for r in self.__data[name] ]
            setattr(self,name,records)

    def get_many(self,name):
        if "no_getter" in self.__has_many[name]:
            return []
        elif "through" in self.__has_many[name]:
            self_ref = utils.snake(self.model.name) + "_id"
            assoc_ref = utils.snake(self.__has_many[name]["model"].name) + "_id"
            assoc = self.__has_many[name]["through"]
            assoc_field = self.__has_many[name]["association"]
            joins = assoc.where({self_ref: self.id}, {"include": assoc_field})
            return [ getattr(j,assoc_field) for j in joins ]
        else:
            reference = utils.snake(self.model.name) + "_id"
            results = self.__has_many[name]["model"].where({reference: self.id})
            return results

    def has_many_generic(self,name,model):
        self.__has_many_generic[name] = { "model": model }
        if name in self.__data:
            records = [ model.record(r) for r in self.__data[name] ]
            setattr(self,name,records)

    def get_many_generic(self,name):
        results = self.__has_many_generic[name]["model"].where({
            "parent_class": self.model.name,
            "parent_id": self.id})
        return results

    def __getattr__(self, name):

        # print("method missing for " + name)

        def __get_one_wrapper(name):
            return self.get_one(name)

        def __get_many_wrapper(name):
            return self.get_many(name)

        def __get_many_generic_wrapper(name):
            return self.get_many_generic(name)

        if self.id == None and name in self.__has_one:
            return None
        elif self.id == None and \
             ( name in self.__has_many or \
               name in self.__has_many_generic ):
            return []
        elif name in self.__has_one:
            return __get_one_wrapper(name)
        elif name in self.__has_many:
            return __get_many_wrapper(name)
        elif name in self.__has_many_generic:
            return __get_many_generic_wrapper(name)
        else:
            raise Exception("Attribute '" + name +
                            "' of " + self.model.name +
                            " not found.")

    def to_json(self,include=[],exclude=[]):

        j = { "rid": self.rid }

        if not type(include) is list:
            raise Exception("include argument must be a list in " + str(type(self)) + ".to_json")

        if not type(exclude) is list:
            raise Exception("exclude argument must be a list in " + str(type(self)) + ".to_json")            

        for property, value in vars(self).items():
            if property not in exclude and \
               not utils.is_record(value) and \
               not re.match(r'\_',property) and \
               not property == 'model' and \
               not property in self.__has_many and \
               not property in self.__has_many_generic and \
               not property in self.__has_one:
                  j[property] = value

        for property in include:
            if type(property) is str:
                value = getattr(self,property)
                if value and property in self.__has_one:
                    j[property] = getattr(self,property).to_json()
                elif value and property in self.__has_many or property in self.__has_many_generic:
                    j[property] = [v.to_json() for v in getattr(self,property)]
            elif type(property) is dict:
                for name, val in property.items():
                    value = getattr(self,name)
                    if value and name in self.__has_one:
                        j[name] = value.to_json(include=val)
                    elif value and name in self.__has_many or name in self.__has_many_generic:
                        j[name] = [v.to_json(include=val) for v in value]

        return j

    def append_association(self,name,value):
        newval = getattr(self,name)
        newval.append(value)
        setattr(self,name, newval)
        return self

    def set_association(self,name,value):
        setattr(self,name, value)
        return self
