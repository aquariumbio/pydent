from marshmallow import SchemaOpts, Schema, post_load, fields, pre_load, pre_dump

from pydent.marshaller.relation import Relation

# attribute to reference the model from the schema
MODEL_CLASS = "model_class"

# attribute to reference the schema from the models
MODEL_SCHEMA = "model_schema"

# class name of the field options for the schema
META = "Meta"

# class name of the field options for the models
MODEL_META = "Fields"

# name of the extra fields parameter
EXTRA_FIELDS = "_loaded_fields"

# attribute key to store relationships
RELATIONSHIPS = "relationships"


class DynamicSchema(Schema):
    """Schema that automatically loads missing values from data"""

    @pre_load
    def add_fields(self, data):
        self.filter_ignored(data)
        self.load_missing(data)
        return data

    @post_load
    def load_model(self, data):
        """Loads the model using the class stored in the schema when 'add_schema' decorator was used."""
        model_class = getattr(self.__class__, MODEL_CLASS)
        model_inst = model_class(data=data)
        setattr(model_inst, EXTRA_FIELDS, self.fields)
        return model_inst

    @pre_dump
    def add_extra_fields_to_dump(self, obj):
        # add extra fields if this object was loaded with extra data (aka if "load_all"=True in model meta)
        if hasattr(obj, EXTRA_FIELDS):
            extra_fields = list(obj._loaded_fields.keys())
            self.opts.additional = set(list(self.opts.additional) + extra_fields)
        return obj

    def load_missing(self, data):
        """Includes missing fields not explicitly defined in the schema"""
        meta = self.__class__.Meta
        more_keys = []
        if meta.load_all:
            for key, val in data.items():
                if key not in self.fields:
                    dump_only = []
                    if hasattr(meta, "dump_only"):
                        dump_only = key in meta.dump_only
                    self.fields[key] = fields.Raw(allow_none=True, dump_only=dump_only)
                    more_keys.append(key)
        setattr(meta, "additional", more_keys)

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


class DefaultMeta(SchemaOpts):
    """Default field options for dynamically generated schemas"""
    load_all = True  # load missing data attributes not explicitly defined during serialization
    strict = True  # throw error during marshalling instead of storing error
    include = {}  # fields to include for serialization/deserialization. Grouped with fields defined in model class
    # explicitly defined fields for serialization/deserialization.
    additional = ()
    # fields to filter during deserialization. These fields will be filtered from the JSON.
    ignore = ()
    load_only = ()  # fields to ignore during serialization
    dump_only = ()  # fields to ignore during deserialization


def add_schema(cls):
    """Decorator that dynamically creates a schema and attaches it to a model."""

    default_meta_props = {key: val for key, val in vars(DefaultMeta).items() if not key.startswith("__")}
    model_meta_relationships = {}

    if hasattr(cls, MODEL_META):
        model_meta = getattr(cls, MODEL_META)
        props = vars(model_meta).items()
        model_meta_props = {key: val for key, val in props if not key.startswith("__")}
        model_meta_fields = {key: val for key, val in model_meta_props.items() if isinstance(val, fields.Field)}

        # combine found fields with "include"
        include = model_meta_props.get("include", {})
        include.update(model_meta_fields)
        model_meta_props["include"] = include

        # collect relationships
        model_meta_relationships = {key: val for key, val in include.items() if isinstance(val, Relation)}

        # update defaults with field options found in model class definition
        default_meta_props.update(model_meta_props)

    # create the meta class
    meta = type(META, (), default_meta_props)

    # create the new schema
    new_schema = type(cls.__name__, (DynamicSchema,), {META: meta, MODEL_CLASS: cls,
                                                       RELATIONSHIPS: model_meta_relationships})
    setattr(cls, MODEL_SCHEMA, new_schema)
    return cls
