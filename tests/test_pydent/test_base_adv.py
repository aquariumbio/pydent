from pydent.marshaller import add_schema
from pydent.relationships import HasMany
from pydent import ModelBase
from pydent.models import (AllowableFieldType,
                           ObjectType, OperationType, SampleType)


def test_attribute_missing(fake_session):

    @add_schema
    class Author(ModelBase):
        fields = dict(books=HasMany("Book", ref="book_id", callback="foo"))

        def __init__(self):
            super().__init__(
                books=None
            )

        def foo(self, *args):
            return [1,2,3]

    class Book(ModelBase):
        pass

    a = Author.load_from({}, fake_session.utils)
    print(a.books)
    print(a.dump())


def test_nested_dump_relations():

    ot = OperationType(name="MyOT")
    aft = AllowableFieldType(object_type=ObjectType(id=1, name="MyOBJ"),
                             sample_type=SampleType(id=2, name="MYSAMPLETYPE"))
    assert isinstance(aft.object_type, ObjectType)
    assert isinstance(aft.sample_type, SampleType)

    assert aft.object_type.id == 1
    assert aft.sample_type.id == 2

    assert aft.object_type_id == 1
    assert aft.sample_type_id == 2

    data = aft.dump()
    data.pop('rid')

    assert data == {
        "id": None,
        "object_type_id": 1,
        "sample_type_id": 2,
        'field_type_id': None
    }