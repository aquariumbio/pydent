import json

from pydent.marshaller.exceptions import MarshallerCallbackNotFoundError, MarshallerRelationshipError
from pydent.marshaller.schema import MODEL_SCHEMA
from pydent.utils import magiclist


class MarshallerBase(object):
    """Base class for marshalling and unmarshalling. Used in conjunction with
    :func:`pydent.marshaller.schema.add_schema`

    Example Usage:


    .. code-block:: python

        from pydent.marshaller import MarshallerBase, add_schema

        @add_schema
        class UserModel(MarshallerBase):
            fields = dict(
                ignore=("password",),
                budgets=Relation("Budget", callback="find_budgets", params=lambda self: self.id)
            )

            def find_budgets(user_id):
                # find budgets with user_id
                pass

        # load from JSON
        u = UserModel.load(user_data)

        # dump to JSON
        u.dump()
    """

    save_attr = True

    @classmethod
    def create_from_json(cls, *args, data=None, **kwargs):
        """
        Special constructor method for instantiating with JSON data

        :param data: json data to update instance attributes
        :type data: dict
        :return: model instance
        :rtype: MarshallerBase (or subclass)
        """
        inst = cls(*args, **kwargs)
        if data is None:
            data = {}
        vars(inst).update(data)
        return inst

    @classmethod
    def get_schema_class(cls):
        """Return the Schema class associated with this model"""
        return getattr(cls, MODEL_SCHEMA)

    @classmethod
    def create_schema_instance(cls, *schema_args, **schema_kwargs):
        """Create a Schema instance for loading or dumping"""
        return cls.get_schema_class()(*schema_args, **schema_kwargs)

    @classmethod
    def get_relationships(cls):
        """Collect the 'Relation' fields"""
        return cls.get_schema_class().relationships

    # TODO: explicitly add schema args and kwargs
    # TODO: add init_args and init_kwargs
    @classmethod
    @magiclist
    def load(cls, *schema_args, **schema_kwargs):
        """Loads an instance from JSON"""
        schema = cls.create_schema_instance(*schema_args, **schema_kwargs)
        return schema.load(*schema_args, **schema_kwargs).data

    def dump(self, *schema_args, **schema_kwargs):
        """Dumps the model instance to JSON"""
        schema = self.__class__.create_schema_instance(*schema_args, **schema_kwargs)
        return schema.dump(self).data

    def dumps(self, *schema_args, **schema_kwargs):
        json_data = self.dump(*schema_args, **schema_kwargs)
        return json.dumps(json_data)

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
                raise MarshallerCallbackNotFoundError("Could not find callback \"{}\" in {} instance"
                                            .format(fxn, self.__class__.__name__))

        # get params; pass in self if param is callable
        fxn_params = self._get_callback_params(field)
        schema_model_name = field.nested
        return fxn(schema_model_name, *fxn_params)

    def _get_callback_params(self, field):
        fxn_params = []
        for param in field.params:
            if callable(param):
                fxn_params.append(param(self))
            else:
                fxn_params.append(param)
        return fxn_params

    def __getstate__(self):
        """Override for pickling objects"""
        return self.dump()

    def __setstate__(self, state):
        """Override for unpickling objects"""
        self.__dict__.update(state)

    def __getattr__(self, item):
        """Retrieves and fullfills relationships if available"""
        relationships = object.__getattribute__(self, "get_relationships")()
        save_attr = object.__getattribute__(self, "save_attr")
        if item in relationships:
            field = relationships[item]
            ret = None
            try:
                ret = self._fullfill(field)
            except AttributeError as e:
                msg = ""
                for i, m in enumerate(e.args):
                    msg += "({}) {}\n".format(i, m)
                msg += "Could not fullfill relationship for {}(instance).{} as relation {}\n".format(self.__class__.__name__, item, field)
                msg += "{}".format(self.dump())
                raise MarshallerRelationshipError(msg)
            if save_attr:
                setattr(self, item, ret)
            return ret
        return object.__getattribute__(self, item)

    def __repr__(self):
        return "<{}>".format(self.__class__.__name__)