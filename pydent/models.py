from pillowtalk import add_schema, One, Many, PillowtalkBase


class AqBase(PillowtalkBase):
    def __init__(self, *args, aqsession=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._session = aqsession

    @property
    def session(self):
        return self._session

    def set_session(self, session):
        if self._session is None:
            self._session = session
        else:
            raise Exception("Cannot reset session for an Aquarium model.")

    def find(self, model_name, id):
        return getattr(self.session, model_name).find(id)


@add_schema
class User(AqBase):
    """An Aquarium User model"""

    FIELDS = ["login", "name"]


@add_schema
class Sample(AqBase):
    """An Aquarium Sample model"""

    FIELDS = ["name"]
    RELATIONSHIPS = [
        One("sample_type", "find Sample.sample_type_id <> SampleType.id")
    ]

    @property
    def sample_type(self):
        return self.session.SampleType.find(self.sample_type_id)


@add_schema
class SampleType(AqBase):
    """An Aquarium SampleType model"""

    FIELDS = ["name"]
    RELATIONSHIPS = [
        Many("samples", "where SampleType.id <> Sample.sample_type_id")
    ]

    @property
    def samples(self):
        return self.session.SampleType.where({"id": self.sample_type_id})


@add_schema
class Item(AqBase):
    """An Aquarium Item model"""

    FIELDS = []
    RELATIONSHIPS = [
        One("sample", "find Item.sample_id <> Sample.id"),
        One("object_type", "find Item.object_type_id <> ObjectType.id")
    ]

    @property
    def object_type(self):
        return self.session.ObjectType.find(self.object_type_id)

    @property
    def sample(self):
        return self.session.Sample.find(self.id)


@add_schema
class ObjectType(AqBase):
    """An Aquarium ObjectType model"""

    FIELDS = ["name"]
    RELATIONSHIPS = [
        Many("items", "where ObjectType.id <> Item.object_type_id")
    ]


@add_schema
class Collection(AqBase):
    """An Aquarium Collection model"""

    FIELDS = []
    RELATIONSHIPS = [
        One("object_type", "where Collection.id <> ObjectType.id")
    ]


@add_schema
class FieldValue(AqBase):
    """An Aquarium FieldValue model"""

    FIELDS = []
    RELATIONSHIPS = [
        One("field_type", "find FieldValue.field_type_id <> FieldType.id"),
        One("allowable_field_type",
            "find FieldValue.allowable_field_type_id <> AllowableFieldType.id"),
        One("item", "find FieldValue.child_item_id <> Item.id"),
        One("sample", "find FieldValue.child_sample_id <> Sample.id"),
        One("operation", "find FieldValue.parent_id <> Operation.id"),
        One("parent_sample", "find FieldValue.parent_id <> Sample.id")
    ]


# TODO: what's the best way to store session information.
# TODO: Instances of objects may want to access the session they came from?
class CodeInterface(object):
    """Mixing for adding code update"""

    def update(self):
        """ Updates code for a OperationType or Library """
        if self.parent_class == "OperationType":
            controller = "operation_types"
        elif self.parent_class == "Library":
            controller = "libraries"
        else:
            raise Exception("No code update controller available.")
        result = self.session.post(controller + "/code", {
            "id": self.parent_id,
            "name": self.name,
            "content": self.content
        })
        if "id" in result:
            self.id = result["id"]
            self.parent_id = result["parent_id"]
            self.updated_at = result["updated_at"]
        else:
            raise Exception("Unable to update code object.")

    def code(self, name):
        latest = [code for code in self.codes
                  if not code.child_id and code.name == name]
        if len(latest) == 1:
            return latest[0]


@add_schema
class Library(CodeInterface, AqBase):
    FIELDS = []
    RELATIONSHIPS = [
        Many("operations", "where Library.operation_id <> Operation.id"),
        Many("codes", "where Library.id <> Code.parent_id"),
    ]

    @property
    def source(self):
        return self.code("source")


@add_schema
class OperationType(AqBase):
    """An Aquarium OperationType model"""

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
        return None


@add_schema
class Code(AqBase):
    """An Aquarium Code Model"""
    FIELDS = []
    RELATIONSHIP = [
        One("operation_type", "find Code.parent_id <> OperationType.id")
    ]


@add_schema
class Operation(AqBase):
    """An Aquarium Operation model"""

    FIELDS = []
    RELATIONSHIPS = [
        One("operation_type", "find Operation.operation_type_id <> OperationType.id")
    ]
