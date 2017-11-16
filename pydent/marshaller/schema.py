from marshmallow import SchemaOpts, Schema, post_load, fields, pre_load, pre_dump

from pydent.marshaller.relation import Relation

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


# TODO: ability to dump hierarchical data 

class DefaultFieldOptions(SchemaOpts):
    """Default field options for dynamically generated schemas"""
    load_all = True  # load missing data attributes not explicitly defined during serialization
    strict = True  # throw error during marshalling instead of storing error
    load_only = ()  # fields to ignore during serialization
    dump_only = ()  # fields to ignore during deserialization

    # fields to include for serialization/deserialization. Grouped with fields defined in model class
    include = {}

    # explicitly defined fields for serialization/deserialization.
    additional = ()

    # fields to filter during deserialization. These fields will be filtered from the JSON.
    ignore = ()


class DynamicSchema(Schema):
    """Schema that automatically loads missing values from data"""

    # Assign default field options
    Meta = DefaultFieldOptions

    @pre_load
    def add_fields(self, data):
        self.filter_ignored(data)
        self.load_missing(data)
        return data

    @post_load
    def load_model(self, data):
        """Loads the model using the class stored in the schema when 'add_schema' decorator was used."""
        model_class = getattr(self.__class__, MODEL_CLASS)

        # additional init parameters
        args = data.get("args", [])
        kwargs = data.get("kwargs", {})

        # instantiate model from class
        model_inst = model_class.create_from_json(*args, data=data, **kwargs)

        # save the extra fields
        setattr(model_inst, EXTRA_FIELDS, self.fields)

        # save raw JSON that created the instance
        model_inst.raw = data
        return model_inst

    @pre_dump
    def add_extra_fields_to_dump(self, obj):
        # add extra fields if this object was loaded with extra data
        if hasattr(obj, EXTRA_FIELDS):
            # copy the declared fields
            declared_fields = dict(self.declared_fields)
            self.declared_fields = declared_fields

            # update the declared fields
            self.declared_fields.update(obj.loaded_fields)
        return obj

    def load_missing(self, data):
        """Includes missing fields not explicitly defined in the schema"""
        meta = self.__class__.Meta
        more_keys = []
        if meta.load_all:
            for key in data.keys():
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


def add_schema(cls):
    """Decorator that dynamically creates a schema and attaches it to a model."""
    default_meta_props = {key: val for key, val in vars(DefaultFieldOptions).items() if not key.startswith("__")}
    model_meta_relationships = {}

    if hasattr(cls, MODEL_META):
        model_meta_props = getattr(cls, MODEL_META)
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
