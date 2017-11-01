from pillowtalk import *

from .aqbase import AqBase
from .session import Session


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


@add_schema
class Collection(AqBase):
    FIELDS = []
    RELATIONSHIPS = [
        One("object_type", "where Collection.id <> ObjectType.id")
    ]


@add_schema
class FieldValue(AqBase):
    FIELDS = []
    RELATIONSHIPS = [
        One("field_type", "find FieldValue.field_type_id <> FieldType.id"),
        One("allowable_field_type", "find FieldValue.allowable_field_type_id <> AllowableFieldType.id"),
        One("item", "find FieldValue.child_item_id <> Item.id"),
        One("sample", "find FieldValue.child_sample_id <> Sample.id"),
        One("operation", "find FieldValue.parent_id <> Operation.id"),
        One("parent_sample", "find FieldValue.parent_id <> Sample.id")
        # TODO: currently Pillowtalks's relationships are unable to distinguish parent_class...
    ]


@add_schema
class OperationType(AqBase):
    FIELDS = []
    RELATIONSHIPS = [
        Many("codes", "where OperationType.id <> Code.parent_id")
    ]

    @property
    def protocol(self):
        return self.code("protocol")

    def code(self, name):
        latest = [code for code in self.codes
                  if not code.child_id and code.name == name]
        if len(latest) == 1:
            return latest[0]
        else:
            return None


class CodeInterface(object):

    def update(self):
        # Todo: make server side controller for code objects
        # since they may not always be tied to specific parent
        # controllers
        if self.parent_class == "OperationType":
            controller = "operation_types"
        elif self.parent_class == "Library":
            controller = "libraries"
        else:
            raise Exception("No code update controller available.")
        s = Session().session
        print(s)
        result = Session().session.post(controller+"/code", {
            "id"     : self.parent_id,
            "name"   : self.name,
            "content": self.content
        })
        if "id" in result:
            self.id = result["id"]
            self.parent_id = result["parent_id"]
            self.updated_at = result["updated_at"]
        else:
            raise Exception("Unable to update code object.")

@add_schema
class Library(CodeInterface, AqBase):

    FIELDS = []
    RELATIONSHIPS = [
        Many("operations", "where Library.operation_id <> Operation.id"),
        Many("codes", "where Library.id <> Code.parent_id")
    ]

    def code(self, name):
        latest = [code for code in self.codes
                  if not code.child_id and code.name == name]
        if len(latest) == 1:
            return latest[0]
        else:
            return None

    @property
    def source(self):
        return self.code("source")


@add_schema
class Code(CodeInterface, AqBase):
    FIELDS = []
    RELATIONSHIP = [
        One("operation_type", "find Code.parent_id <> OperationType.id")
    ]

@add_schema
class Operation(AqBase):

    FIELDS = []
    RELATIONSHIPS = [
        One("operation_type", "find Operation.operation_type_id <> OperationType.id")
    ]