from pydent import ModelBase
from pydent.marshaller import add_schema
from pydent.models import AllowableFieldType
from pydent.models import ObjectType
from pydent.models import OperationType
from pydent.models import SampleType
from pydent.relationships import HasMany


def test_attribute_missing(fake_session):
    @add_schema
    class Author(ModelBase):
        fields = dict(books=HasMany("Book", ref="book_id", callback="foo"))

        def __init__(self):
            super().__init__(books=None)

        def foo(self, *args):
            return []

    @add_schema
    class Book(ModelBase):
        pass

    a = Author.load_from({}, fake_session)
    books1 = a.books
    vid = id(books1)
    books2 = a.books
    vid2 = id(books2)

    vid3 = id(a.__deserialized_data["books"])
    vid4 = id(a.__serialized_data["books"])
    books3 = a.books
    assert id(books1) == id(books2), "books attribute ids must be identical"
    assert id(books2) == id(books3)


def test_nested_dump_relations():

    ot = OperationType(name="MyOT")
    aft = AllowableFieldType(
        object_type=ObjectType(id=1, name="MyOBJ"),
        sample_type=SampleType(id=2, name="MYSAMPLETYPE"),
    )
    assert isinstance(aft.object_type, ObjectType)
    assert isinstance(aft.sample_type, SampleType)

    assert aft.object_type.id == 1
    assert aft.sample_type.id == 2

    assert aft.object_type_id == 1
    assert aft.sample_type_id == 2

    data = aft.dump()
    data.pop("rid")

    assert data == {
        "id": None,
        "object_type_id": 1,
        "sample_type_id": 2,
        "field_type_id": None,
    }


def test_nested_dump_uri(fake_session):
    @add_schema
    class Book(ModelBase):
        pass


    @add_schema
    class Author(ModelBase):
        fields = dict(books=HasMany("Book", ref="book_id", callback="foo"))

        def __init__(self):
            super().__init__(books=None)

        def foo(self, *args):
            return [Book.load_from({'id': 10}, fake_session)]

    a = Author.load_from({'id': 3}, fake_session)

    data = a.dump(include='books', include_uri=True)
    assert data['__uri__'] == fake_session.url + "/" + "authors/3"
    assert data['books'][0]['__uri__'] == fake_session.url + "/" + "books/10"


def test_nested_model_type(fake_session):

    @add_schema
    class Book(ModelBase):
        pass

    @add_schema
    class Author(ModelBase):
        fields = dict(books=HasMany("Book", ref="book_id", callback="foo"))

        def __init__(self):
            super().__init__(books=None)

        def foo(self, *args):
            return [Book.load_from({'id': 10}, fake_session)]

    a = Author.load_from({'id': 3}, fake_session)

    data = a.dump(include='books', include_model_type=True)
    assert data['__model__'] == "Author"
    assert data['books'][0]['__model__'] == "Book"

