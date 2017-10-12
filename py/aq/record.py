import aq
import re

_next_rid = 0;

def new_rid():
    global _next_rid
    _next_rid += 1
    return _next_rid

class Record:

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
            self_ref = aq.utils.snake(self.model.name) + "_id"
            assoc_ref = aq.utils.snake(self.__has_many[name]["model"].name) + "_id"
            assoc = self.__has_many[name]["through"]
            assoc_field = self.__has_many[name]["association"]
            joins = assoc.where({self_ref: self.id}, {"include": assoc_field})
            return [ getattr(j,assoc_field) for j in joins ]
        else:
            reference = aq.utils.snake(self.model.name) + "_id"
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

    def to_json(self):
        j = {}
        for property, value in vars(self).items():

            if property in self.__has_one or aq.utils.is_record(value):
                j[property] = value.to_json()
            elif property in self.__has_many or \
                property in self.__has_many_generic:
                j[property] = [v.to_json() for v in value]
            elif not re.match(r'\_',property) and not property == 'model':
                j[property] = value

        return j

    def append_association(self,name,value):
        newval = getattr(self,name)
        newval.append(value)
        setattr(self,name, newval)
        return self

    def set_association(self,name,value):
        setattr(self,name, value)
        return self
