from pillowtalk import *
from .aqbase import AqBase


@add_schema
class User(AqBase):

    FIELDS = ["login", "name"]


@add_schema
class Sample(AqBase):

    FIELDS = ["name"]
    RELATIONSHIPS = [
        One("sample_type", "find Sample.sample_type_id <> SampleType.id")
    ]


@add_schema
class SampleType(AqBase):

    FIELDS = ["name"]
    RELATIONSHIPS = [
        Many("samples", "where SampleType.id <> Sample.sample_type_id")
    ]


@add_schema
class Item(AqBase):

    FIELDS = []
    RELATIONSHIPS = [
        One("sample", "find Item.sample_id <> Sample.id"),
        One("object_type", "find Item.object_type_id <> ObjectType.id")
    ]


@add_schema
class ObjectType(AqBase):

    FIELDS = ["name"]
    RELATIONSHIPS = [
        Many("items", "where ObjectType.id <> Item.object_type_id")
    ]