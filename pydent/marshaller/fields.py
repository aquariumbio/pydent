"""
Fields
"""

from abc import ABC, abstractmethod
from enum import Enum, auto

from pydent.marshaller.descriptors import CallbackAccessor, MarshallingAccessor, RelationshipAccessor, Placeholders
from pydent.marshaller.exceptions import AllowNoneFieldValidationError, RunTimeCallbackAttributeError
from pydent.marshaller.registry import ModelRegistry
from pydent.marshaller.utils import make_signature_str


class FieldABC(ABC):
    """
    Field abstract base class
    """

    @abstractmethod
    def serialize(self):
        pass

    @abstractmethod
    def deserialize(self):
        pass

    @abstractmethod
    def _serialize(self):
        pass

    @abstractmethod
    def _deserialize(self):
        pass


class Field(FieldABC):
    """A serialization/deserialization field."""

    ACCESSOR = MarshallingAccessor

    def __init__(self, many=None, data_key=None, allow_none=None, default=Placeholders.DEFAULT):
        """A standard field. Performs no functions on serialized and
        deserialized data.

        :param many: whether to treat serializations and deserializations as a per-item basis in a list
        :type many: bool
        :param data_key: the data_key, or attribute name, of this field. Calling this as an attribute to the registered
        nested should return this field's descriptor.
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
        self.objtype = None
        self.data_key = data_key
        self.allow_none = allow_none
        self.default = default

    def set_data_key(self, key):
        self.data_key = key

    def _deserialize(self, owner, data):
        return data

    def _serialize(self, owner, data):
        return data

    def deserialize(self, owner, data):
        if data is None:
            if not self.allow_none:
                raise AllowNoneFieldValidationError("None is not allowed for field '{}'".format(self.data_key))
            return None
        if self.many:
            # TODO: This if statement patches a bug in which accessing many attibutes returned different lists
            # return [self._deserialize(owner, d) for d in data]
            # deserialize in place
            for i, x in enumerate(data):
                data[i] = self._deserialize(owner, x)
            return data
        return self._deserialize(owner, data)

    def serialize(self, owner, data):
        if data is None:
            if not self.allow_none:
                raise AllowNoneFieldValidationError("None is not allowed for field '{}'".format(self.data_key))
            return None
        if self.many:
            return [self._serialize(owner, d) for d in data]
        return self._serialize(owner, data)

    def register(self, name, objtype):
        """Registers the field to a nested class. Instantiates the corresponding
        descriptor (i.e. accessor)

        :param name: name of the field
        :type name: basestring
        :param objtype: the nested class to register the field to
        :type objtype: SchemaModel
        :return: None
        :rtype: None
        """

        self.objtype = objtype
        if name not in objtype.__dict__:
            key = name
            if self.data_key:
                key = self.data_key
            setattr(objtype, name, self.ACCESSOR(name=key, field=self, accessor=objtype._data_key,
                                                 deserialized_accessor=objtype._deserialized_key, default=self.default))

    def __str__(self):
        return "<{cls} key='{objtype}.{key}' many={many} allow_none={allow_none}>".format(
            cls=self.__class__.__name__,
            key=self.data_key,
            many=self.many,
            allow_none=self.allow_none,
            objtype=self.objtype
        )


class Nested(Field):
    """Represents a field that returns another nested instance."""

    def __init__(self, nested, many=None, data_key=None, allow_none=None, lazy=None):
        """Nested relationship initializer.

        :param nested: the nested name of nested field. Should exist in the ModelRegistery.
        :type nested: SchemaModel
        :param many: whether to treat serializations and deserializations as a per-item basis in a list
        :type many: bool
        :param data_key: the data_key, or attribute name, of this field. Calling this as an attribute to the registered
        nested should return this field's descriptor.
        :type data_key: basestring
        :param allow_none: whether to return None if None is received in deserialization or serializaiton methods
        :type allow_none: bool
        :param lazy: if set to True (default), perform lazy serialization and deserialization. If the data received
        by `deserialize` is the expected nested, return that data. If the object
        recieved by `serialize` is not the expected nested, return that data.
        :type lazy:
        """

        self.nested = nested
        if lazy is None:
            self.lazy = True
        if allow_none is None:
            allow_none = True
        super().__init__(many, data_key, allow_none)

    def get_model(self):
        return ModelRegistry.get_model(self.nested)

    # TODO: how to properly handle lazy deserialization? (dict vs expected object)
    def _deserialize(self, owner, data):
        if data is None and self.allow_none:
            return None
        elif self.lazy and isinstance(data, self.get_model()):
            return data
        return self.get_model()._set_data(data, session=owner.session)

    # TODO: how to properly handle lazy serialization? (dict vs expected object)
    def _serialize(self, owner, obj):
        if obj is None and self.allow_none:
            return None
        elif self.lazy and not isinstance(obj, self.get_model()):
            return obj
        return obj._get_data()


class Callback(Field):
    """Make a callback when called."""

    class __FLAGS(Enum):
        SELF = auto()

    SELF = __FLAGS.SELF
    ACCESSOR = CallbackAccessor

    def __init__(self, callback, callback_args=None, callback_kwargs=None, cache=False, data_key=None, many=None,
                 allow_none=None, always_dump=False):
        """A Callback field initializer.

        :param callback: name of the callback function or a callable. If a name, the name should exist
        as a function in the owner instance. Invalid callback signatures are captures on class creation.
        :type callback: callable|basestring
        :param callback_args: a tuple of arguments to use in the callback. If any of the callback arguments  or
        values of the callback kwargs are callable, the owner will be passed to the callable. The owner instance will
        replace any arguments that are `Callback.SElF`
        :type callback_args: tuple
        :param callback_kwargs: a dictionary of kwargs to use in the callback
        :type callback_kwargs: dict
        :param cache: whether to cache the result using `setattr` on the owner instance. This will initialize the
        serialization and deserialization procedures detailed in the corresponding field/descriptor.
        :type cache: bool
        :param many: whether to treat serializations and deserializations as a per-item basis in a list
        :type many: bool
        :param allow_none: whether to return None if None is received in deserialization or serializaiton methods
        :type allow_none: bool
        :param data_key: the data_key, or attribute name, of this field. Calling this as an attribute to the registered
        nested should return this field's descriptor.
        :param always_dump: if True, this field will be serialized by default
        :type always_dump: bool
        """

        super().__init__(many, data_key, allow_none)
        self.callback = callback
        self.always_dump = always_dump
        if callback_args is None:
            callback_args = tuple()
        elif not isinstance(callback_args, (list, tuple)):
            callback_args = (callback_args,)
        self.callback_args = tuple(callback_args)
        if callback_kwargs is None:
            callback_kwargs = {}
        self.callback_kwargs = dict(callback_kwargs)
        self.cache = cache

    def _callback_signature(self, args=None, kwargs=None):
        if args is None:
            args = self.callback_args
        if kwargs is None:
            kwargs = self.callback_kwargs
        return "{func}{args}".format(
            func=self.callback,
            args=make_signature_str(args, kwargs)
        )

    def get_callback_args(self, owner):
        """Processes the callback args"""
        args = []
        try:
            for a in self.callback_args:
                if a is self.SELF:
                    args.append(owner)
                elif callable(a):
                    args.append(a(owner))
                else:
                    args.append(a)
        except AttributeError as e:
            raise RunTimeCallbackAttributeError(
                "There was an error retrieving callback arguments for '{sig}' due to:\n{e}".format(
                    sig=self._callback_signature(),
                    e="{}: {}".format(e.__class__.__name__, e)
                )) from e
        return args

    def get_callback_kwargs(self, owner):
        """Processes the callback kwargs"""
        kwargs = {}
        try:
            for k, v in self.callback_kwargs.items():
                if callable(v):
                    kwargs[k] = v(owner)
                elif v is self.SELF:
                    kwargs[k] = owner
                else:
                    kwargs[k] = v
        except AttributeError as e:
            raise RunTimeCallbackAttributeError(
                "There was an error retrieving callback keyword arguments for '{func}(args)' due to:\n{e}".format(
                    func=self.callback,
                    args=self._callback_signature(),
                    e="{}: {}".format(e.__class__.__name__, e)
                )) from e
        return kwargs

    def fullfill(self, owner, cache=None):
        """Calls the callback function using the owner object. A
        Callback.SELF arg value will be replaced to be equivalent to the
        owner instance model.

        :param owner: the owning object
        :type owner: SchemaModel
        :return: function result
        :rtype: any
        """

        if callable(self.callback):
            func = self.callback
        else:
            func = getattr(owner, self.callback)

        callback_args = self.get_callback_args(owner)
        callback_kwargs = self.get_callback_kwargs(owner)

        try:
            val = func(*tuple(callback_args), **callback_kwargs)
        except AttributeError as e:
            raise RunTimeCallbackAttributeError(
                "There was an calling '{signature}' due to:\n{e}".format(
                    signature=self._callback_signature(callback_args, callback_kwargs),
                    e="{}: {}".format(e.__class__.__name__, e)
                )) from e
        if cache is None:
            cache = self.cache
        if cache:
            self.cache_result(owner, val)
        return val

    def cache_result(self, owner, val):
        setattr(owner, self.data_key, val)

    def _deserialize(self, owner, data):
        raise NotImplementedError("_deserialize is not implemented for field {}".format(self))

    def deserialize(self, *args, **kwargs):
        raise NotImplementedError("deserialize is not implemented for field {}".format(self))


class Relationship(Callback):
    """
    A composition (Callback/Nested) field that uses a callback to retrieve a model.
    """

    ACCESSOR = RelationshipAccessor

    def __init__(self, nested, callback, callback_args=None, callback_kwargs=None, cache=True, data_key=None, many=None,
                 allow_none=None, always_dump=False):
        """
        Relationship initializer

        :param nested: the nested name of nested field. Should exist in the ModelRegistery.
        :type nested: SchemaModel
        :param callback: name of the callback function or a callable. If a name, the name should exist
        as a function in the owner instance. Invalid callback signatures are captures on class creation.
        :type callback: callable|basestring
        :param callback_args: a tuple of arguments to use in the callback. If any of the callback arguments  or
                                values of the callback kwargs are callable, the owner will be passed to the callable. The owner instance will
                                replace any arguments that are `Callback.SElF`
        :type callback_args: tuple
        :param callback_kwargs: a dictionary of kwargs to use in the callback
        :type callback_kwargs: dict
        :param cache: whether to cache the result using `setattr` on the owner instance. This will initialize the
        serialization and deserialization procedures detailed in the corresponding field/descriptor.
        :type cache: bool
        :param many: whether to treat serializations and deserializations as a per-item basis in a list
        :type many: bool
        :param data_key: the data_key, or attribute name, of this field. Calling this as an attribute to the registered
        nested should return this field's descriptor.
        """

        super().__init__(callback, callback_args, callback_kwargs, cache, data_key, many, allow_none, always_dump)
        self.nested_field = Nested(nested, many, data_key)
        self.nested = nested
        self.callback_args = tuple([nested] + list(self.callback_args))

    def deserialize(self, owner, val):
        return self.nested_field.deserialize(owner, val)

    def serialize(self, owner, obj):
        return self.nested_field.serialize(owner, obj)


class Alias(Callback):
    """A shallow alias to another field. """

    def __init__(self, field_name):
        """
        Alias field initialize. Exposes a shallow alias to another field that can be accessed by
        a different attribute key.

        :param field_name: the key of the other field
        :type field_name: basestring
        """

        self.alias = field_name
        super().__init__(lambda s: getattr(s, field_name), callback_args=(Callback.SELF,), always_dump=True, data_key=field_name)
