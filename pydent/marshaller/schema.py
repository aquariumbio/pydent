from marshmallow import SchemaOpts, Schema
from marshmallow import post_load, pre_load, pre_dump, post_dump
from pydent.marshaller.field_extensions import fields

# attribute to reference the model from the schema
MODEL_CLASS = "model_class"

# attribute to reference the schema from the models
MODEL_SCHEMA = "model_schema"

# class name of the field options for the schema
META = "Meta"

# class name of the field options for the models
MODEL_META = "fields"

# name of the extra fields parameter
EXTRA_FIELDS = "loaded_fields"

# attribute key to store relationships
RELATIONSHIPS = "relationships"


class DefaultFieldOptions(SchemaOpts):
    """
        Serialization/Deserialization field options class (:class:`SchemaOpts`).
        Determines how data is handled.
        There are lots of available options, how you use them will depend on
        your particular application.

        **Field options:**

        - ``load_all``: Include all attributes from the loaded data in the
                        deserialized object
        - ``ignore``: List or tuple of attributes to ignore in the deserialization
                        process
        - ``load_only``: Tuple or list of fields to exclude from serialized results.
        - ``dump_only``: Tuple or list of fields to exclude from deserialization
        - ``exclude``: Tuple or list of fields to exclude in the serialized result.
            Nested fields can be represented with dot delimiters.
        - ``include``: Dictionary of additional fields to include in the schema. It is
            usually better to define fields as class variables, but you may need to
            use this option, e.g., if your fields are Python keywords. May be an
            `OrderedDict`.
        - ``additional``: Tuple or list of fields to include *in addition* to the
            explicitly declared fields. ``additional`` and ``fields`` are
            mutually-exclusive options.
        - ``strict``: If `True`, raise errors during marshalling rather than
            storing them.

        **Additional field options (inherited from :class:`SchemaOpts`)**

        - ``fields``: Tuple or list of fields to include in the serialized result.
        - ``dateformat``: Date format for all DateTime fields that do not have their
            date format explicitly specified.
        - ``render_module``: Module to use for `loads` and `dumps`. Defaults to
            `json` from the standard library.
            Defaults to the ``json`` module in the stdlib.
        - ``ordered``: If `True`, order serialization output according to the
            order in which fields were declared. Output of `Schema.dump` will be a
            `collections.OrderedDict`.
        - ``index_errors``: If `True`, errors dictionaries will include the index
            of invalid items in a collection.
    """

    # Default field options
    load_all = True
    strict = True
    load_only = ()
    dump_only = ()
    include = {}
    additional = ()
    ignore = ()


class DynamicSchema(Schema):
    """Schema that automatically loads missing values from data. For more information about
    the baseclass Schema, take a look at the `Schema documentation
    <https://marshmallow.readthedocs.io/en/latest/api_reference.html#schema>`_ for marshmallow.
     """

    # Assign default field options
    Meta = DefaultFieldOptions
    relationships = {}

    def __init__(self, *args, only=None, exclude=(), relations=(), all_relations=False,
                 strict=None, many=False,
                 context=None, load_only=(), dump_only=(), partial=False, prefix='',
                 **kwargs):
        """
        Custom Schema for marshalling and demarshalling models


        :param tuple only: A list or tuple of fields to serialize. If `None`, all
            fields will be serialized. Nested fields can be represented with dot delimiters.
        :param tuple exclude: A list or tuple of fields to exclude from the
            serialized result. Nested fields can be represented with dot delimiters.
        :param tuple relations: A list or tuple of fields to include during
            serialization
        :param boolean all_relations: whether to dump all relationship during deserialization
        :param str prefix: Optional prefix that will be prepended to all the
            serialized field names.
        :param bool strict: If `True`, raise errors if invalid data are passed in
            instead of failing silently and storing the errors.
        :param bool many: Should be set to `True` if ``obj`` is a collection
            so that the object will be serialized to a list.
        :param dict context: Optional context passed to :class:`fields.Method` and
            :class:`fields.Function` fields.
        :param tuple load_only: A list or tuple of fields to skip during serialization
        :param tuple dump_only: A list or tuple of fields to skip during
            deserialization, read-only fields
        :param bool|tuple partial: Whether to ignore missing fields. If its value
            is an iterable, only missing fields listed in that iterable will be
            ignored.
        """

        relations, load_only, only = self.fix_schema_parameters(
            all_relations, relations, load_only, only)
        super().__init__(*args, only=only, exclude=exclude, prefix=prefix, strict=strict,
                         many=many, context=context, load_only=load_only, dump_only=dump_only,
                         partial=partial, **kwargs)
        self.dump_relations = relations

    def fix_schema_parameters(self, dump_all_relations, dump_relations, load_only, only):
        if isinstance(only, str):
            only = {only}
        if isinstance(dump_relations, str):
            dump_relations = {dump_relations}
        if isinstance(load_only, str):
            load_only = {load_only}

        # include relations in only
        if only:
            only = set(list(only) + list(dump_relations))
            only_relations = only.intersection(self.relationships.keys())
            dump_relations = set(dump_relations).union(only_relations)

        # by default, relationships are 'load_only', meaning they will not be serialized
        load_only = set(list(load_only) + list(self.relationships.keys()))

        # if there are any dump_relations keys, remove them from 'load_only' so
        # they can be serialized
        self.all_relations = dump_all_relations
        if dump_all_relations:
            dump_relations = tuple(self.relationships.keys())
        load_only = tuple(set(load_only) - set(dump_relations))

        return dump_relations, load_only, only

    @pre_load
    def add_fields(self, data):
        """Filter out ignored and load missing values"""
        # a little bit hacky, but if the data being loaded is already
        # deserialized, just reserialize it...
        if isinstance(data, getattr(self.__class__, MODEL_CLASS)):
            data = data.dump()
        self.filter_ignored(data)
        if isinstance(data, dict):
            self.load_missing(data.keys())
        return data

    def save_extra_fields(self, model_instance):
        setattr(model_instance, EXTRA_FIELDS, self.fields)

    def load_missing(self, data_keys):
        """Includes missing fields not explicitly defined in the schema"""
        meta = self.__class__.Meta
        more_keys = []
        if meta.load_all:
            for key in data_keys:
                if key not in self.fields:
                    dump_only = []
                    if hasattr(meta, "dump_only"):
                        dump_only = key in meta.dump_only
                    self.fields[key] = fields.Raw(
                        allow_none=True, dump_only=dump_only)
                    more_keys.append(key)
        setattr(meta, "additional", more_keys)

    @post_load
    def load_model(self, data):
        """
        Loads the model using the class stored in the schema when 'add_schema'
        decorator was used.
        """
        model_class = getattr(self.__class__, MODEL_CLASS)
        if model_class == data.__class__:
            return data

        # additional init parameters
        args = data.get("args", [])
        kwargs = data.get("kwargs", {})

        # instantiate model from class
        model_inst = model_class.create_from_json(*args, data=data, **kwargs)

        self.save_extra_fields(model_inst)

        # save raw JSON that created the instance
        model_inst.raw = data
        return model_inst

    def add_extra_fields(self, extra_fields):
        # copy the declared fields
        declared_fields = dict(self.declared_fields)
        self.declared_fields = declared_fields
        self.declared_fields.update(extra_fields)

    @pre_dump
    def add_extra_fields_to_dump(self, obj):
        # add extra fields if this object was loaded with extra data
        extra_fields = {}
        if hasattr(obj, EXTRA_FIELDS):
            extra_fields.update(obj.loaded_fields)

        for field_name in self.relationships.keys():
            if field_name in self.dump_relations:
                # if self._depth < self.dump_depth:
                #     extra_fields[field_name] = self.relationships[field_name]
                extra_fields[field_name] = self.relationships[field_name]
        self.add_extra_fields(extra_fields)
        return obj

    @post_dump
    def remove_ignored_from_dump(self, data):
        return self.filter_ignored(data)

    def filter_ignored(self, data):
        """Removes ignored fields from the JSON data"""
        meta = self.Meta
        ignore = []
        if hasattr(meta, "ignore"):
            ignore = meta.ignore
        for ignored in ignore:
            if ignored in data:
                del data[ignored]
        return data


def add_schema(cls):
    """
    Class Decorator that dynamically creates a :class:`DynamicSchema` and attaches it
    to a :class:`pydent.marshaller.MarshallerBase` or its subclass.

    Example usage:

    .. code-block:: python

        @add_schema
        class MyModel(MarshallerBase)
            fields = dict(
                ignore=("password",)
                # additional field options
            )

            def foo(self):
                pass
    """
    default_meta_props = {key: val for key, val in vars(
        DefaultFieldOptions).items() if not key.startswith("__")}
    model_meta_relationships = {}

    if hasattr(cls, MODEL_META):
        model_meta_props = getattr(cls, MODEL_META)
        model_meta_fields = {key: val for key, val in model_meta_props.items(
        ) if isinstance(val, fields.Field)}

        # combine found fields with "include"
        include = model_meta_props.get("include", {})
        include.update(model_meta_fields)
        model_meta_props["include"] = include

        # collect relationships
        model_meta_relationships = {
            key: val for key, val in include.items() if isinstance(val, fields.Relation)}

        # update defaults with field options found in model class definition
        default_meta_props.update(model_meta_props)

    # create the meta class
    meta = type(META, (), default_meta_props)

    # create the new schema
    new_schema = type(cls.__name__, (DynamicSchema,), {META: meta, MODEL_CLASS: cls,
                                                       RELATIONSHIPS: model_meta_relationships})
    new_schema.__name__ = new_schema.__name__ + "Schema"
    setattr(cls, MODEL_SCHEMA, new_schema)
    return cls
