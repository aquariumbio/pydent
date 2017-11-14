from pydent.marshaller.schema import MODEL_SCHEMA
from pydent.marshaller.exceptions import ModelNotFoundError, CallbackNotFoundError


class ModelRegistry(type):
    """Stores a list of models that can be accessed by name."""
    models = {}

    def __init__(cls, name, bases, selfdict):
        """Class initializer. Called when a class is 'subclassed.' Saves model to the registry"""
        super().__init__(name, bases, selfdict)
        if not name == "Base":
            ModelRegistry.models[name] = cls

    @staticmethod
    def get_model(model_name):
        """Gets model by model_name"""
        if model_name not in ModelRegistry.models:
            raise ModelNotFoundError("Model \"{}\" not found.".format(model_name))
        else:
            return ModelRegistry.models[model_name]


class MarshallerBase(metaclass=ModelRegistry):
    """Base class for marshalling and unmarshalling"""

    save_attr = True

    def __init__(self, data=None):
        if data is None:
            data = {}
        vars(self).update(data)

    @classmethod
    def schema(cls):
        """Return the Schema class associated with this model"""
        return getattr(cls, MODEL_SCHEMA)

    @classmethod
    def get_schema(cls, *schema_args, **schema_kwargs):
        """Create a Schema instance for loading or dumping"""
        return cls.schema()(*schema_args, **schema_kwargs)

    @classmethod
    def get_relationships(cls):
        """Collect the 'Relation' fields"""
        return cls.schema().relationships

    @classmethod
    def load(cls, *schema_args, **schema_kwargs):
        """Loads an instance from JSON"""
        schema = cls.get_schema(*schema_args, **schema_kwargs)
        return schema.load(*schema_args, **schema_kwargs).data

    def dump(self, *schema_args, **schema_kwargs):
        """Dumps the model instance to JSON"""
        schema = self.__class__.get_schema(*schema_args, **schema_kwargs)
        return schema.dump(self).data

    def dumps(self, *schema_args, **schema_kwargs):
        json_data = self.dump(*schema_args, **schema_kwargs)
        return str(json_data)

    def _fullfill(self, field):
        """
        Fullfills a relationship with a callback.

        :param field: relationship field
        :type field: Relation instance
        :return:
        :rtype:
        """

        # get function
        fxn = field.callback
        if not callable(fxn):
            try:
                fxn = getattr(self, fxn)
            except AttributeError:
                raise CallbackNotFoundError("Could not find callback \"{}\" in {} instance"
                                            .format(fxn, self.__class__.__name__))

        # get params; pass in self if param is callable
        fxn_params = []
        for param in field.params:
            if callable(param):
                fxn_params.append(param(self))
            else:
                fxn_params.append(param)
        schema_model_name = field.nested
        return fxn(schema_model_name, *fxn_params)

    def __getattr__(self, item):
        relationships = object.__getattribute__(self, "get_relationships")()
        save_attr = object.__getattribute__(self, "save_attr")
        if item in relationships:
            field = relationships[item]
            ret = self._fullfill(field)
            if save_attr:
                setattr(self, item, ret)
            return ret
        return object.__getattribute__(self, item)

    def __repr__(self):
        return "<{}>".format(self.__class__.__name__, self.__dict__)