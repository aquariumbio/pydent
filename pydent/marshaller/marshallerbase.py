import json
import warnings
from copy import deepcopy

from pydent.marshaller.exceptions import (MarshallerCallbackNotFoundError,
                                          MarshallerRelationshipError)
from pydent.marshaller.schema import MODEL_SCHEMA
from pydent.utils import pformat


class MarshallerBase(object):
    """
    Base class for marshalling and unmarshalling. Used in conjunction with
    :func:`pydent.marshaller.schema.add_schema`

    Example Usage:


    .. code-block:: python

        from pydent.marshaller import MarshallerBase, add_schema

        @add_schema
        class UserModel(MarshallerBase):
            fields = dict(
                ignore=("password",),
                budgets=Relation("Budget", callback="find_budgets",
                                 params=lambda self: self.id)
            )

            def find_budgets(user_id):
                # find budgets with user_id
                pass

        # load from JSON
        u = UserModel.load(user_data)

        # dump to JSON
        u.dump()
    """

    model_schema = None
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
        schema_class = cls.get_schema_class()
        if schema_class:
            schema = cls.get_schema_class()(*schema_args, **schema_kwargs)
            schema.context = schema_kwargs
            return schema

    @classmethod
    def get_relationships(cls):
        """
        Get the name: relationship
        (:class:`pydent.marshaller.relation.Relation`)
        dictionary
        """
        schema_class = cls.get_schema_class()
        if schema_class:
            return cls.get_schema_class().relationships
        return {}

    @property
    def relationships(self):
        """
        Get the name: relationship
        (:class:`pydent.marshaller.relation.Relation`)
        dictionary.
        """
        return self.__class__.get_relationships()

    @classmethod
    def load(cls, data, *args, only=None, exclude=(), all_relations=False,
             prefix='', strict=None, many=False, relations=(), load_only=(),
             dump_only=(), partial=False, **kwargs):
        """Loads the model instance from JSON. For parameter options, refer to
        :class:`pydent.marshaller.schema.DynamicSchema`"""

        schema_kwargs = dict(
            only=only,
            exclude=exclude,
            relations=relations,
            all_relations=all_relations,
            prefix=prefix,
            strict=strict,
            many=many,
            load_only=load_only,
            dump_only=dump_only,
            partial=partial,
        )
        schema_kwargs.update(kwargs)

        schema = cls.create_schema_instance(*args, **schema_kwargs)
        if schema:
            return schema.load(data).data

        # TODO: violates an invariant, throw an exception
        warnings.warn(
            "Cannot dump! No schema attached to '{}'".format(cls.__name__))

    def dump(self, only=None, include=(), exclude=(), relations=(),
             all_relations=False, prefix='', strict=None,
             many=False, load_only=(), dump_only=(),
             partial=False, **kwargs):
        """Dumps the model instance to a String. For parameter options, refer
        to :class:`pydent.marshaller.schema.DynamicSchema`

        :param tuple only: A list or tuple of fields to serialize. If `None`,
                all non relationship fields will be serialized.
        :param str|list|tuple|set|dict include: Nested relationships to include
                in the serialization. This accepts a string (for one nested
                relationship), a tuple (for multiple relationships) or a dict
                (for recursively applied serialization). A dictionary of dump
                options 'opts' can be recursively applied to each serialization.
        :param tuple exclude: A list or tuple of fields to exclude from the
                serialized result. Nested fields can be represented with dot
                delimiters.
        :param tuple relations: A list or tuple of fields to include during
                serialization. Unlike 'include', this will not be applied
                recursively
        :param boolean all_relations: whether to dump all relationship during
                deserialization
        :param str prefix: Optional prefix that will be prepended to all the
                serialized field names.
        :param bool strict: If `True`, raise errors if invalid data are passed
                in instead of failing silently and storing the errors.
        :param bool many: Should be set to `True` if ``obj`` is a collection so
                that the object will be serialized to a list.
        :param dict context: Optional context passed to :class:`fields.Method`
                and :class:`fields.Function` fields.
        :param tuple load_only: A list or tuple of fields to skip during
                serialization
        :param tuple dump_only: A list or tuple of fields to skip during
                deserialization, read-only fields
        :param bool|tuple partial: Whether to ignore missing fields. If its
                value is an iterable, only missing fields listed in that
                iterable will be ignored.


        Example Usage using 'only' to dump only particular relationships

        .. code-block:: python

            # dump 'name' and nested relationship 'sample_type'
            mydump = mymodel.dump(only=('name', 'sample_type'))

        Example Usage using 'include' to dump nested relationships:

        .. code-block:: python

            # dump nested relationships 'sample_type' and 'samples' in 'sample_type'
            # for 'sample_type' dump only 'name' in addition to 'samples'
            mydump = mymodel.dump(include={'sample_type': { 'samples': {}, 'opts': {'only': ['name']} } })

        """
        schema_kwargs = dict(
            only=only,
            exclude=exclude,
            relations=relations,
            all_relations=all_relations,
            prefix=prefix,
            strict=strict,
            many=many,
            load_only=load_only,
            dump_only=dump_only,
            partial=partial,
        )
        kwargs = deepcopy(kwargs)
        kwargs.update(deepcopy(schema_kwargs))

        # str to set
        if isinstance(include, str):
            include = {include}

        # update kwargs from opts
        kwargs = deepcopy(kwargs)
        if isinstance(include, dict):
            opts = include.get('opts', {})
            kwargs.update(opts)

        def dump_model(model):
            """
            Tries to dump model using dumping parameters
            """
            if isinstance(model, MarshallerBase):
                _include = {}
                if isinstance(include, dict):
                    _include = include.get(key, {})
                model = model.dump(include=_include)
            return model

        dumped = self._dump(**kwargs)
        for key in include:
            if key in self.get_relationships():
                field = self.get_relationships()[key]
                val = None
                model = getattr(self, key)
                if isinstance(model, list):
                    models = [dump_model(m) for m in model]
                    val = models
                else:
                    val = dump_model(model)
                if field.dump_to:
                    key = field.dump_to
                dumped[key] = val
        return dumped

    def _dump(self, *args, **kwargs):
        """Dump helper"""

        schema = self.__class__.create_schema_instance(*args, **kwargs)
        if schema:
            return schema.dump(self).data

        # TODO: throw an exception. this is an invariant
        warnings.warn("Cannot dump! No schema attached to '{}'".format(
            self.__class__.__name__))

    def dumps(self, *schema_args, **schema_kwargs):
        """
        Dumps the model instance to a String. For parameter options, refer
        to :class:`pydent.marshaller.schema.DynamicSchema`
        """
        json_data = self.dump(*schema_args, **schema_kwargs)
        return json.dumps(json_data)

    def _fullfill(self, field):
        """
        Fullfills a relationship with a callback.

        :param field: relationship field
        :type field: Relation
        :return: model that satisfies the relationship
        :rtype: MarshallerBase
        """

        # get function
        callback = field.callback
        if not callable(callback):
            try:
                callback = getattr(self, callback)
            except AttributeError as error:
                msg = "Could not find callback \"{}\" in {} instance".format(
                    callback, self.__class__.__name__)
                error.args = tuple(list(error.args) + [msg])
                raise MarshallerCallbackNotFoundError(error)

        # get params; pass in self if param is callable
        fxn_args = self._get_callback_args(field)
        fxn_kwargs = self._get_callback_kwargs(field)
        schema_model_name = field.nested
        return callback(schema_model_name, *fxn_args, **fxn_kwargs)

    def _get_callback_args(self, field):
        fxn_params = []
        for param in field.callback_args:
            if callable(param):
                fxn_params.append(param(self))
            else:
                fxn_params.append(param)
        return fxn_params

    def _get_callback_kwargs(self, field):
        if field.callback_kwargs is None:
            return {}
        kwargs = {}
        for k, v in field.callback_kwargs.items():
            if callable(v):
                kwargs[k] = v(self)
            else:
                kwargs[k] = v
        return kwargs

    def __getstate__(self):
        """Override for pickling objects"""
        return self.dump()

    def __setstate__(self, state):
        """Override for unpickling objects"""
        self.__dict__.update(state)

    def __getattribute__(self, name):
        """Override attribute accessor to attempt to fullfill relationships.

        * If the returned attribute is None or [] and the attribute name is in
        the list of relationships, Trident will attempt to fullfill that relationship.
        * If AttributeError or TypeError is raise, return the default value"""
        res = object.__getattribute__(self, name)
        if res is None:
            relationships = object.__getattribute__(
                self, "get_relationships")()
            if name in relationships:
                try:
                    res = self.__getattr__(name)
                except AttributeError:
                    pass
                except TypeError:
                    pass
        return res

    def __getattr__(self, item):
        """
        Retrieves and fullfills relationships if available. This method runs
        only if the given attribute is not found.
        """
        relationships = object.__getattribute__(self, "get_relationships")()
        save_attr = object.__getattribute__(self, "save_attr")
        if item in relationships:
            field = relationships[item]
            ret = None
            try:
                # try to fullfill the relationships
                ret = self._fullfill(field)
            except AttributeError as error:
                # display warning
                msg = "\n"
                msg += "Could not fullfill relationship for {}(instance).{} as relation {}\nReasons:\n".format(
                    self.__class__.__name__, item, field)
                for index, message in enumerate(error.args):
                    msg += "({}) {}\n".format(index, message)
                error.args = tuple(list(error.args) + [msg])
                # warnings.warn(' '.join(error.args))
            if save_attr:
                setattr(self, item, ret)
            return ret
        raise MarshallerRelationshipError(
            "'{}' model has no attribute '{}'. Attribute was not found in list of relationships: {}".format(
                self.__class__.__name__, item,
                ', '.join(relationships.keys())))

    def _relations_to_json(self):
        """
        Dump relations to a dictionary.
        If attribute is None, return the Relation instance.
        """
        dumped = {}
        for field_name, field in self.get_relationships().items():
            val = None
            try:
                val = object.__getattribute__(self, field_name)
            except AttributeError:
                pass
            if val is None:
                val = field
            dumped[field_name] = val
        return dumped

    def _to_dict(self, *args, **kwargs):
        """
        Prints the model instance in a nice format.
        See :func:`pydent.marshaller.marshallerbase.dump`

        :param args: dump arguments
        :param kwargs: dump arguments
        :return:
        """
        dumped = self._relations_to_json()
        _dumped = self.dump(*args, **kwargs)
        if _dumped:
            for key, val in _dumped.items():
                if val is not None or key not in dumped:
                    dumped[key] = val
        return dumped

    def print(self, *args, **kwargs):
        print(pformat(self._to_dict(*args, **kwargs)))

    def __str__(self):
        return pformat(self._to_dict())

    def __repr__(self):
        return "<{}>".format(self.__class__.__name__)
