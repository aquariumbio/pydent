"""Model base class."""
import functools
import inspect
from copy import deepcopy
from typing import Any
from typing import Dict
from typing import List
from typing import Tuple
from typing import Union

from pydent.marshaller.descriptors import DataAccessor
from pydent.marshaller.exceptions import SchemaException
from pydent.marshaller.exceptions import SchemaModelException
from pydent.marshaller.fields import Callback
from pydent.marshaller.registry import ModelRegistry
from pydent.marshaller.schema import DynamicSchema
from pydent.marshaller.schema import SchemaRegistry


def add_schema(cls):
    """Decorator that dynamically attaches a schema to a model."""

    if not issubclass(cls, SchemaModel):
        raise SchemaException("Model must be a subclaass of '{}'".format(SchemaModel))
    new_schema = SchemaRegistry(
        SchemaRegistry.make_schema_name(cls.__name__),
        (DynamicSchema,),
        {"_model_class": cls},
    )
    new_schema.register(cls)
    return cls


class SchemaModel(metaclass=ModelRegistry):
    """A Schema class that holds information on
    serialization/deserialization."""

    __slots__ = [ModelRegistry._data_key, ModelRegistry._deserialized_key, "__dict__"]

    def __init__(self, data=None):
        """The model initializer.

        :param data: data to add to the model
        :type data: dict
        """
        if data is None:
            data = {}
        if not getattr(self, ModelRegistry._data_key, None):
            setattr(self, ModelRegistry._data_key, data)
        if not getattr(self, ModelRegistry._deserialized_key, None):
            setattr(self, ModelRegistry._deserialized_key, {})
        self.add_data(data)

    @property
    def model_schema(self):
        """Returns the attached model schema.

        :return: the model's schema class
        :rtype: DynamicSchema
        """
        return getattr(self.__class__, "model_schema", None)

    def add_data(self, data):
        """Initializes fake attributes that correspond to data."""
        if not self.model_schema:
            filepath = ""
            try:
                filepath = inspect.getfile(self.__class__)
            except Exception:
                pass
            raise SchemaModelException(
                "Cannot initialize a {} without a {}. "
                "Use '@{}' to decorate the class definition for '{}' located in {}".format(
                    SchemaModel.__name__,
                    DynamicSchema.__name__,
                    add_schema.__name__,
                    self.__class__.__name__,
                    filepath,
                )
            )
        if data is not None:
            self.__class__.model_schema.init_data_accessors(self, data)

    def _get_data(self):
        """Return the model's data."""
        return getattr(self, self.__class__._data_key)

    def _get_deserialized_data(self):
        """Return the deserialized model data."""
        return getattr(self, self.__class__._deserialized_key)

    def get_deserialized(self, name):
        """Get deserialized data by name.

        .. deprecated:: 0.1.5a7
            method will be removed in 0.2.
            Use self._get_deserialized_data[name] instead.

        :param name: name of attribute
        :return:
        """
        return self._get_deserialized_data()[name]

    def is_deserialized(self, name: str) -> bool:
        """Check if a given key has already been deserialized.

        .. versionadded:: 0.1.5a7
            Method added

        :param name: name of the attribute
        :return: True if key has been deserialized.
        """
        data = self._get_deserialized_data()
        accessor = self.fields[name]
        if name in data and data[name] is not accessor.ACCESSOR.HOLDER:
            return True
        return False

    def reset_field(self, name: str):
        """Reset the field descriptor to its placeholder value, returning the
        behavior.

        .. versionadded:: 0.1.5a7
            Method added to reset deserialized attributes

        :param name: name of the attribute
        :return: None
        """
        del self._get_deserialized_data()[name]

    @classmethod
    def _set_data(cls, data, calling_obj=None):
        instance = SchemaModel.__new__(cls)
        SchemaModel.__init__(instance, data)
        return instance

    @staticmethod
    def _keys_to_dict(keys):
        if keys is None:
            return {}
        elif isinstance(keys, str):
            return {keys: None}
        elif isinstance(keys, dict):
            return dict(keys)
        else:
            return {k: None for k in keys}

    @classmethod
    def _dump(
        cls,
        obj,
        only: Union[str, List[str], Tuple[str], Dict[str, Any]] = None,
        include: Union[str, List[str], Tuple[str], Dict[str, Any]] = None,
        ignore: Union[str, List[str], Tuple[str], Dict[str, Any]] = None,
        **kwargs,
    ) -> dict:
        if not issubclass(type(obj), SchemaModel):
            return obj

        only = cls._keys_to_dict(only)
        include = cls._keys_to_dict(include)
        ignore = cls._keys_to_dict(ignore)

        data = {}

        serialized_data = obj._get_data()

        include_and_only = set(include).union(set(only))

        for fname in include_and_only:
            getattr(obj, fname)

        keys = set(serialized_data.keys())
        keys = keys.difference(set(ignore))
        if only:
            keys = keys.intersection(set(only))

        model_fields = obj.__class__.model_schema.fields

        callback_fields = []
        always_dump = []
        for fname, field in model_fields.items():
            if hasattr(field, "nested") or issubclass(type(field), Callback):
                callback_fields.append(fname)
            if getattr(field, "always_dump", None):
                always_dump.append(fname)

        include_and_only = include_and_only.union(set(always_dump))
        callback_keys = include_and_only.intersection(set(callback_fields))
        callback_keys = callback_keys.difference(set(ignore))

        data_keys = keys.difference(set(callback_fields))

        for key in data_keys:
            data[key] = serialized_data[key]
        for key in callback_keys:
            field = model_fields[key]
            val = getattr(obj, key)
            dump_kwargs = dict(
                include=include.pop(key, None),
                only=only.pop(key, None),
                ignore=ignore.pop(key, None),
            )
            dump_kwargs.update(kwargs)
            dump = functools.partial(cls._dump, **dump_kwargs)
            if getattr(model_fields[key], "nested", None) and model_fields[key].many:
                if isinstance(val, list):
                    data[field.data_key] = [dump(v) for v in val]
            else:
                data[field.data_key] = dump(val)
        return data

    def dump(
        self,
        only: Union[str, List[str], Tuple[str], Dict[str, Any]] = None,
        include: Union[str, List[str], Tuple[str], Dict[str, Any]] = None,
        ignore: Union[str, List[str], Tuple[str], Dict[str, Any]] = None,
    ) -> dict:
        """Dump/serializes the model to a json-like dictionary.

        :param only: restricts dump/serialization to the provided keys
        :type only: basestring|list|tuple|dict
        :param include: include any callback fields in the dump/serialization
        :type include: basestring|list|tuple|dict
        :param ignore: ignores fields in the dump/serialization
        :type ignore: basestring|list|tuple|dict
        :return: the serialized data
        :rtype: dict
        """
        return deepcopy(self._dump(self, only=only, include=include, ignore=ignore))

    # def __dir__(self):
    #     return ['a']

    @classmethod
    def load(cls, data):
        """Deserialize the data to a model.

        :param data: data to deserialize
        :type data: dict
        :return: the deserialized model
        :rtype: SchemaModel
        """
        return cls._set_data(data)

    def __setstate__(self, state):
        """Overrides how models are unpickled.

        The default way pickling works by dumping the __dict__ along
        with the class definition. Since the way data is handle in the
        marshaller object involves dynamic creation of descriptors,
        these are not properly handled upon load. Here we will create
        these descriptors upon unpickling. Unlike serialized data,
        deserialized data is handled explicitly using 'fields' in the
        schema/model definition, it is not necessary to do anything with
        these descriptors.
        """
        self.__dict__ = state

        # add data accessors
        data = state[ModelRegistry._data_key]
        for k in data:
            if k not in self.__class__.__dict__:
                setattr(self.__class__, k, DataAccessor(k, ModelRegistry._data_key))
