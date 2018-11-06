from pydent.marshaller.exceptions import SchemaException
from pydent.marshaller.schema import DynamicSchema, SchemaRegistry
from pydent.marshaller.fields import Callback
from pydent.marshaller.registry import ModelRegistry
from copy import deepcopy

def add_schema(cls):
    """Dynamically attaches a schema to a model.

    :param cls:
    :type cls:
    :return:
    :rtype:
    """

    if not issubclass(cls, SchemaModel):
        raise SchemaException("Model must be a subclaass of '{}'".format(SchemaModel))
    new_schema = SchemaRegistry(SchemaRegistry.make_schema_name(cls.__name__), (DynamicSchema,), {})
    new_schema.register(cls)
    return cls


class SchemaModel(metaclass=ModelRegistry):

    # def __new__(cls, *args, **kwargs):
    #     instance = super(SchemaModel, cls).__new__(cls, *args, **kwargs)
    #     instance.pre_initialization_hook(dict())
    #     return instance
    fields = dict()
    __slots__ = [ModelRegistry._data_key, ModelRegistry._deserialized_key, '__dict__']

    def __init__(self):
        self.pre_initialization_hook({})
        self.raw = None
        self.post_initialization_hook()

    def pre_initialization_hook(self, data):
        """Initializes fake attributes that correspond to data."""
        setattr(self, ModelRegistry._data_key, data)
        setattr(self, ModelRegistry._deserialized_key, {})
        self.raw = dict(data)
        self.__class__.model_schema.init_data_accessors(self, data)

    def post_initialization_hook(self):
        """Post initialization setup."""
        pass

    @classmethod
    def set_data(cls, data):
        model_instance = cls.__new__(cls)
        model_instance.pre_initialization_hook(data)
        model_instance.post_initialization_hook()
        return model_instance

    def get_data(self):
        return getattr(self, self.__class__._data_key)

    def get_deserialized_data(self):
        return getattr(self, self.__class__._deserialized_key)

    @classmethod
    def load(cls, data):
        return cls.set_data(dict(data))

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

    def _dump(self, only=None, include=None, ignore=None):
        only = self._keys_to_dict(only)
        include = self._keys_to_dict(include)
        ignore = self._keys_to_dict(ignore)

        callback_fields = [k for k, v in self.fields.items() if issubclass(type(v), Callback)]
        data = {}

        serialized_data = self.get_data()

        for fname in set(include).union(set(only)):
            getattr(self, fname)
        keys = set(serialized_data.keys())
        keys = keys.difference(set(ignore))
        if only:
            keys = keys.intersection(set(only))
        callback_keys = keys.intersection(set(callback_fields))
        data_keys = keys.difference(set(callback_fields))

        for key in data_keys:
            data[key] = serialized_data[key]
        for key in callback_keys:
            data[key] = getattr(self, key)._dump(
                include=include.pop(key, None),
                only=only.pop(key, None),
                ignore=ignore.pop(key, None)
            )
        return data

    def dump(self, only=None, include=None, ignore=None):
        return deepcopy(self._dump(only=only, include=include, ignore=ignore))

