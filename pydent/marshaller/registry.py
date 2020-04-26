"""Model and schema registry meta-classes."""
from collections import defaultdict
from pprint import pformat

from pydent.marshaller.exceptions import ModelRegistryError
from pydent.marshaller.exceptions import SchemaRegistryError
from pydent.utils.loggable import condense_long_lists
from pydent.utils.logging_helpers import did_you_mean


class SchemaRegistry(type):
    """Stores a list of models that can be accessed by name."""

    schemas = {}  # the registry of Schemas instantiated
    _fields = None  # list of fields instantiated
    _model_class = None  # reference to model class the schema is attached to
    BASE = "DynamicSchema"

    def __init__(cls, name, bases, selfdict):
        """Saves model to the registry."""
        super().__init__(name, bases, selfdict)
        if bases != () and name != SchemaRegistry.BASE:
            if name in SchemaRegistry.schemas:
                raise SchemaRegistryError(
                    "Cannot register '{}' since it already exists.".format(name)
                )
            SchemaRegistry.schemas[name] = cls

    @property
    def model_class(cls):
        """The registered model class."""
        return cls._model_class

    @property
    def fields(cls):
        """The shcmea fields."""
        return cls._fields

    @property
    def grouped_fields(cls):
        """Fields grouped by their base classes.

        Returns empty list of base class not in fields.
        """
        grouped = defaultdict(dict)
        for fname, field in cls.fields.items():
            mro = field.__class__.__mro__
            for b in mro[:-2]:
                grouped[b.__name__][fname] = field
        return grouped

    @staticmethod
    def make_schema_name(name):
        """Makes a Schema class name from a model name (appending 'Schema' to
        name)"""
        return name + "Schema"

    @staticmethod
    def get_schema(name):
        """Gets model by model_name."""
        if name not in SchemaRegistry.schemas:
            raise SchemaRegistryError(
                'Schema "{}" not found in SchemaRegistry. Available schemas:\n{}'.format(
                    name, ",".join(SchemaRegistry.schemas.keys())
                )
            )
        else:
            return SchemaRegistry.schemas[name]

    @staticmethod
    def get_model_schema(model_name):
        """Gets a model schema from a model name."""
        return SchemaRegistry.get_schema(SchemaRegistry.make_schema_name(model_name))


class ModelRegistry(type):
    """Stores list of all models instantiated from the SchemaModel base."""

    models = {}  # the dictionary of model classes instantiated
    _model_schema = None  # the class attribute to store the model_classes Schema class
    _fields_key = "fields"  # the class level attribute key to instantiate model fields
    _data_key = "__serialized_data"  # the attribute key used to store serialized data
    _deserialized_key = (
        "__deserialized_data"  # the attribute key used to store serialized data
    )
    BASE = "SchemaModel"

    def __init__(cls, name, bases, selfdict):
        """Saves model to the registry."""
        super().__init__(name, bases, selfdict)
        if bases != () and bases[0].__name__ != ModelRegistry.BASE:
            ModelRegistry.models[name] = cls

    @property
    def model_schema(cls):
        """Returns the class's schema."""
        return cls._model_schema

    @classmethod
    def did_you_mean_model(cls, model_name, fallback=True):
        model_names = list(cls.models.keys())
        available_models = ", ".join(model_names)
        msg = did_you_mean(model_name, model_names)
        if not msg and fallback:
            return "Available models: {}".format(pformat(available_models))
        return msg

    @classmethod
    def get_model(cls, name):
        """Gets a model class by name."""
        if name not in ModelRegistry.models:
            raise ModelRegistryError(
                "Model '{}' not found in registry.\n{}".format(
                    name, cls.did_you_mean_model(name)
                )
            )
        return cls.models[name]
