from pydent.marshaller.descriptors import CallbackAccessor, MarshallingAccessor
from pydent.marshaller.exceptions import AllowNoneFieldValidationError
from pydent.marshaller.registry import ModelRegistry
from enum import Enum, auto

class Field(object):
    """A serialization/deserialization field."""

    ACCESSOR = MarshallingAccessor

    def __init__(self, many=None, data_key=None, allow_none=None):
        """A standard field. Performs no functions on serialized and
        deserialized data.

        :param many: whether to treat serializations and deserializations as a per-item basis in a list
        :type many: bool
        :param data_key: the data_key, or attribute name, of this field. Calling this as an attribute to the registered
        model should return this field's descriptor.
        :type data_key: basestring
        :param allow_none: whether to return None if None is received in deserialization or serializaiton methods
        :type allow_none: bool
        :raises AllowNoneFieldValidationError if None is received in serialize and deserialized methods
        and self.allow_none == False
        """
        if allow_none is None:
            allow_none = True
        if many is None:
            many = False
        self.many = many
        self.data_key = data_key
        self.allow_none = allow_none

    def set_data_key(self, key):
        self.data_key = key

    def _deserialize(self, data):
        if data is None:
            raise AllowNoneFieldValidationError("None is not allowed for field '{}'".format(self.data_key))
        return data

    def _serialize(self, data):
        if data is None and not self.allow_none:
            raise AllowNoneFieldValidationError("None is not allowed for field '{}'".format(self.data_key))
        return data

    def deserialize(self, owner, data):
        try:
            data = self._deserialize(data)
        except AllowNoneFieldValidationError as e:
            if self.allow_none:
                return None
            else:
                raise e
        return data

    def serialize(self, owner, data):
        try:
            data = self._serialize(data)
        except AllowNoneFieldValidationError as e:
            if self.allow_none:
                return None
            else:
                raise e
        return data

    def register(self, name, objtype):
        """Registers the field to a model class. Instantiates the corresponding
        descriptor (i.e. accessor)

        :param name: name of the field
        :type name: basestring
        :param objtype: the model class to register the field to
        :type objtype: SchemaModel
        :return: None
        :rtype: None
        """
        if name not in objtype.__dict__:
            key = name
            if self.data_key:
                key = self.data_key
            setattr(
                objtype, name,
                self.ACCESSOR(
                    name=key, field=self, accessor=objtype._data_key, deserialized_accessor=objtype._deserialized_key))


class Nested(Field):
    """Represents a field that returns another model instance."""

    def __init__(self, model, many=None, data_key=None, allow_none=None, lazy=None):
        """Nested relationship initializer.

        :param model: the model name of nested field. Should exist in the ModelRegistery.
        :type model: SchemaModel
        :param many: whether to treat serializations and deserializations as a per-item basis in a list
        :type many: bool
        :param data_key: the data_key, or attribute name, of this field. Calling this as an attribute to the registered
        model should return this field's descriptor.
        :type data_key: basestring
        :param allow_none: whether to return None if None is received in deserialization or serializaiton methods
        :type allow_none: bool
        :param lazy: if set to True (default), perform lazy serialization and deserialization. If the data received
        by `deserialize` is the expected model, return that data. If the object
        recieved by `serialize` is not the expected model, return that data.
        :type lazy:
        """
        self.model = model
        if lazy is None:
            self.lazy = True
        if allow_none is None:
            allow_none = True
        super().__init__(many, data_key, allow_none)

    def get_model(self):
        return ModelRegistry.get_model(self.model)

    # TODO: how to properly handle lazy deserialization? (dict vs expected object)
    def deserialize(self, owner, data):
        data = super().deserialize(owner, data)
        if data is None and self.allow_none:
            return None
        elif self.lazy and isinstance(data, self.get_model()):
            return data
        return self.get_model().set_data(data)

    # TODO: how to properly handle lazy serialization? (dict vs expected object)
    def serialize(self, owner, obj):
        obj = super().serialize(owner, obj)
        if self.lazy and not isinstance(obj, self.get_model()):
            return obj
        if obj is None and self.allow_none:
            return None
        return obj.get_data()


class Callback(Field):
    """Make a callback when called.

    Option to cache or not cache (i.e. like an attribute)
    """

    class ARGS(Enum):
        SELF = auto()

    ACCESSOR = CallbackAccessor

    def __init__(self, callback, callback_args=None, callback_kwargs=None, cache=True, data_key=None, many=None, allow_none=None):
        """A Callback field initializer.

        :param callback: name of the callback function or a callable. If a name, the name should exist
        as a function in the owner instance. Invalid callback signatures are captures on class creation.
        :type callback: callable|basestring
        :param callback_args: a tuple of arguments to use in the callback
        :type callback_args: tuple
        :param callback_kwargs: a dictionary of kwargs to use in the callback
        :type callback_kwargs: dict
        :param cache: whether to cache the result using `setattr` on the owner instance. This will initialize the
        serialization and deserialization procedures detailed in the corresponding field/descriptor.
        :type cache: bool
        :param many: whether to treat serializations and deserializations as a per-item basis in a list
        :type many: bool
        :param data_key: the data_key, or attribute name, of this field. Calling this as an attribute to the registered
        model should return this field's descriptor.
        """
        super().__init__(many, data_key, allow_none)
        self.callback = callback
        if callback_args is None:
            callback_args = tuple()
        elif not isinstance(callback_args, (list, tuple)):
            callback_args = (callback_args,)
        self.callback_args = tuple(callback_args)
        if callback_kwargs is None:
            callback_kwargs = {}
        self.callback_kwargs = dict(callback_kwargs)
        self.cache = cache

    def fullfill(self, owner):
        """Calls the callback function using the owner object. A Callback.ARGS.SELF arg value will be replaced
        to be equivalent to the owner instance model.

        :param owner: the owning object
        :type owner: SchemaModel
        :return: function result
        :rtype: any
        """
        if callable(self.callback):
            func = self.callback
        else:
            func = getattr(owner, self.callback)

        # process the callback args
        callback_args = []
        for a in self.callback_args:
            if a is self.ARGS.SELF:
                callback_args.append(owner)
            else:
                callback_args.append(a)

        val = func(*tuple(callback_args), **self.callback_kwargs)
        if self.cache:
            setattr(owner, self.data_key, val)
        return val

    def deserialize(self, owner, data):
        return self.fullfill(owner)


class Relation(Callback, Nested):
    """Returns a Nested model using a callback function."""

    def __init__(self, model, callback, callback_args=None, callback_kwargs=None, cache=True, data_key=None, many=None, allow_none=None):
        self.model = model
        super().__init__(callback, callback_args, callback_kwargs, cache, data_key, many, allow_none)
        Nested.__init__(self, model, many, data_key)
        self.callback_args = tuple([model] + list(self.callback_args))

    def deserialize(self, owner, data):
        """Deserializes JSON data into a Nested model.

        :param owner: the object that owns the field
        :type owner: SchemaModel
        :param data: the json data
        :type data: dict
        :return: the deserialized object
        :rtype: SchemaModel
        """
        data = super().deserialize(owner, data)
        return Nested.deserialize(self, owner, data)

    def serialize(self, owner, obj):
        """Serializes an object to a dictionary.

        :param owner: the object that owns the field
        :type owner: SchemaModel
        :param obj: the object
        :type obj: SchemaModel
        :return: serialized data
        :rtype: dict
        """
        return Nested.serialize(self, owner, obj)

JSON = Field