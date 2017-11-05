"""Define the record class"""

import re
import aq

NEXT_RID = 0

def new_rid():
    """Make a new record id"""
    global NEXT_RID
    NEXT_RID += 1
    return NEXT_RID

class Record:

    """Record class from which all specific records are derived"""

    def __init__(self, model, data):
        """Initialize a new record"""
        self.model = model
        self.id = None
        self.__data = data
        self.__has_one = {}
        self.__has_many = {}
        self.__has_many_generic = {}
        self._rid = None
        for key in data:
            setattr(self, key, data[key])

    @property
    def rid(self):
        """Make or get the record id"""
        if not self._rid:
            self._rid = new_rid()
        return self._rid

    def has_one(self, name, model, opts={}):
        """Declare that this record 'has one' association for the given model,
        named by 'name'
        """
        self.__has_one[name] = {"model": model}
        self.__has_one[name].update(opts)
        if name in self.__data:
            setattr(self, name, model.record(self.__data[name]))
            # also delete attr name = "_id" if it exists

    def get_one(self, name):
        """Get the one associated record, named by name, assuming 'has_one' has
        been called
        """
        if "reference" in self.__has_one[name]:
            reference = self.__has_one[name]["reference"]
        else:
            reference = name + "_id"
        fid = getattr(self, reference)
        if fid:
            result = self.__has_one[name]["model"].find(fid)
        else:
            result = None
        setattr(self, name, result)
        return result

    def has_many(self, name, model, opts={}):
        """Declare that this record 'has many' associations for the given model,
        named by 'name'
        """
        self.__has_many[name] = {"model": model}
        self.__has_many[name].update(opts)
        if name in self.__data:
            records = [model.record(r) for r in self.__data[name]]
            setattr(self, name, records)

    def get_many(self, name):
        """Get the many associated records, named by name, assuming 'has_many'
        has been called
        """
        if "no_getter" in self.__has_many[name]:
            return []
        elif "through" in self.__has_many[name]:
            self_ref = aq.utils.snake(self.model.name) + "_id"
            assoc = self.__has_many[name]["through"]
            assoc_field = self.__has_many[name]["association"]
            joins = assoc.where({self_ref: self.id}, {"include": assoc_field})
            return [getattr(j, assoc_field) for j in joins]
        else:
            reference = aq.utils.snake(self.model.name) + "_id"
            results = self.__has_many[name]["model"].where(
                {reference: self.id})
            return results

    def has_many_generic(self, name, model):
        """Declare that this record 'has many' associations for the given model,
        named by 'name'. This version of has_many assumes that there is a
        'parent_class' and 'parent_id', which are used when setting up generic
        associations (such as code or data_association) in rails.
        """
        self.__has_many_generic[name] = {"model": model}
        if name in self.__data:
            records = [model.record(r) for r in self.__data[name]]
            setattr(self, name, records)

    def get_many_generic(self, name):
        """Get the many associated records, named by name, assuming
        'has_many_generic' has been called
        """
        results = self.__has_many_generic[name]["model"].where({
            "parent_class": self.model.name,
            "parent_id": self.id})
        return results

    def __getattr__(self, name):
        """Get an association by name automagically (assumes has_* method has
        been called at some point)
        """
        # print("method missing for " + name)

        def __get_one_wrapper(name):
            return self.get_one(name)

        def __get_many_wrapper(name):
            return self.get_many(name)

        def __get_many_generic_wrapper(name):
            return self.get_many_generic(name)

        if self.id is None and name in self.__has_one:
            return None
        elif self.id is None and \
            (name in self.__has_many or
             name in self.__has_many_generic):
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

    def is_association(self, prop):
        """Returns true if prop is the name of an association"""
        return prop in self.__has_many or \
               prop in self.__has_many_generic or \
               prop in self.__has_one

    def to_json(self, include=[], exclude=[]):
        """Convert the record to json"""

        j = {"rid": self.rid}

        if not isinstance(include, list):
            raise Exception(
                "include argument must be a list in " + str(type(self)) + ".to_json")

        if not isinstance(exclude, list):
            raise Exception(
                "exclude argument must be a list in " + str(type(self)) + ".to_json")

        for prop, value in vars(self).items():
            if prop not in exclude and \
               not aq.utils.is_record(value) and \
               not re.match(r'\_', prop) and \
               not prop == 'model' and \
               not self.is_association(prop):
                j[prop] = value

        for prop in include:
            if isinstance(prop, str):
                value = getattr(self, prop)
                if value and prop in self.__has_one:
                    j[prop] = getattr(self, prop).to_json()
                elif value and prop in self.__has_many or prop in self.__has_many_generic:
                    j[prop] = [v.to_json() for v in getattr(self, prop)]
            elif isinstance(prop, dict):
                for name, val in prop.items():
                    value = getattr(self, name)
                    if value and name in self.__has_one:
                        j[name] = value.to_json(include=val)
                    elif value and name in self.__has_many or name in self.__has_many_generic:
                        j[name] = [v.to_json(include=val) for v in value]

        return j

    def append_association(self, name, value):
        """Append the association named 'name' with value 'value'"""
        newval = getattr(self, name)
        newval.append(value)
        setattr(self, name, newval)
        return self

    def set_association(self, name, value):
        """Set an association directly"""
        setattr(self, name, value)
        return self
