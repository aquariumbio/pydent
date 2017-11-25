import pytest
from marshmallow import fields
from pydent.marshaller import MarshallerBase
from pydent.marshaller import Relation, add_schema
from pydent.marshaller.exceptions import MarshallerCallbackNotFoundError, MarshallerRelationshipError
from pydent.marshaller.schema import MODEL_SCHEMA


def test_relationship_access():
    """Relationships should behave just like other fields. Relationships inherit fields.Field, and
    so should behave just like other fields. This test makes sure they are found in the 'relationships'
    in the schema and get included in the fields in the schema."""

    @add_schema
    class MyModel(MarshallerBase):
        fields = dict(
            field4=fields.Field(),
            field5=Relation(None, None, None),
            something=5,
            additional=("field1", "field2"),
            include={
                "field3": fields.Field(),
                "field6": Relation(None, None, None)
            }
        )

        def __init__(self):
            pass

    # Should be exactly 2 relationships, one in "include" and one in class variable
    assert len(MyModel.get_relationships()) == 2

    # Test access to relationships
    schema = getattr(MyModel, MODEL_SCHEMA)
    relationships = getattr(schema, "relationships")

    # make sure relationships are found in the 'relationships' dictioanry
    assert "field5" in relationships
    assert "field6" in relationships

    # make sure other fields are not in relationships
    assert "field1" not in relationships
    assert "field4" not in relationships

    # make sure relationships are in the schema fields
    assert "field5" in schema().fields
    assert "field6" in schema().fields


def test_basic_callback():
    """Relations can use a callback from the model that instantiates it. All callbacks expect
     a model name as the first parameter.
     This callback returns the model name that was passed into it."""
    model_name = "AnyModelName"

    @add_schema
    class MyModel(MarshallerBase):
        fields = dict(
            myrelation=Relation(model_name, callback="test_callback", params=())
        )

        def test_callback(self, model_name):
            return model_name

    m = MyModel.load({})
    assert m.myrelation == model_name


def test_callback_with_params():
    """When my relation is called as an attribute, 'test_callback' should get called
    with params (model_name, 1, 2, 3) passed in. Expected result is x + y + z == 6"""
    model_name = "AnyModelName"

    @add_schema
    class MyModel(MarshallerBase):
        fields = dict(
            myrelation=Relation(model_name, callback="test_callback", params=(1, 2, 3))
        )

        def test_callback(self, model_name, x, y, z):
            return x + y + z

    m = MyModel.load({})
    assert m.myrelation == 6


def test_callback_with_lambda():
    """When my relation is called as an attribute, 'test_callback' should get called. Since
    the params is a lambda (a callable), the lambda will pass in the model instance. The expected
    result is that a tuple (self.x, self.y) == (4,5) will get passed in. The expected result is 4*5 == 20
    with params (model_name, lambda self: (self.x, self.y) passed in. """
    model_name = "AnyModelName"

    @add_schema
    class MyModel(MarshallerBase):
        fields = dict(
            myrelation=Relation(model_name, callback="test_callback",
                                params=lambda self: (self.x, self.y))
        )

        def test_callback(self, model_name, _xy):
            x, y = _xy
            return x * y

    m = MyModel.load({"x": 4, "y": 5})
    assert m.myrelation == 20


def test_alternative_callback():
    """Callables can be used in lieu of function names. In this case, an alternative callback
    is used and is expected to return the model_name passed in."""

    model_name = "AnyModelName"

    def alternative_callback(name):
        return name

    @add_schema
    class MyModel(MarshallerBase):
        fields = dict(
            myrelation=Relation(model_name, callback=alternative_callback, params=())
        )

    m = MyModel.load({"x": 4, "y": 5})
    assert m.myrelation == model_name


def test_callback_with_lambda_with_alternative_callback():
    """When my relation is called as an attribute, alternative_callback should get called. Since
    the params is a lambda (a callable), the lambda will pass in the model instance. The expected
    result is that a tuple (self.x, self.y) == (4,5) will get passed in. The expected result is 5-4 == 1
    with params (model_name, lambda self: (self.x, self.y) passed in. """
    model_name = "AnyModelName"

    def alternative_callback(model_name, _xy):
        x, y = _xy
        return y - x

    @add_schema
    class MyModel(MarshallerBase):
        fields = dict(
            myrelation=Relation(model_name, callback=alternative_callback,
                                params=lambda self: (self.x, self.y))
        )

        def test_callback(self, model_name, _xy):
            x, y = _xy
            return x * y

    m = MyModel.load({"x": 4, "y": 5})
    assert m.myrelation == 1


def test_raises_MarshallerCallbackNotFoundError():
    """If callback doesn't exist, raises a CallbackNotFoundError"""

    @add_schema
    class MyModel(MarshallerBase):
        fields = dict(
            myrelation=Relation("lkjlfj", callback="callback",
                                params=lambda self: (self.x, self.y))
        )

    m = MyModel.load({"x": 4, "y": 5})
    with pytest.raises(MarshallerCallbackNotFoundError):
        assert m.myrelation == 1


def test_deserialize_relationship():
    """If the nested relationship is available, deserialize the data"""

    @add_schema
    class Author(MarshallerBase):
        fields = dict(
            books=Relation("Book", many=True, callback="get_books", params=())
        )

        def get_books(self):
            pass

    @add_schema
    class Book(MarshallerBase):
        fields = dict(
            author=Relation("Author", callback="get_author", params=())
        )

        def get_author(self):
            pass

    author_data = {
        "name": "Fyodor Dostoevsky",
        "books": [
            {"title": "Demons", "year": 1871},
            {"title": "The Idiot", "year": 1868}
        ]
    }

    a = Author.load(author_data)
    assert a.name == "Fyodor Dostoevsky"
    assert isinstance(a.books[0], Book)
    assert len(a.books) == 2

def test_raise_MarshallerRelationshipError():
    """We expect an error to be raised since the MyModel instance will
    be missing an 'x' attribute, which is needed for the test callback"""
    model_name = "AnyModelName"

    @add_schema
    class MyModel(MarshallerBase):
        fields = dict(
            myrelation=Relation(model_name, callback="test_callback",
                                params=lambda self: (self.x, self.y))
        )

        def test_callback(self, model_name, _xy):
            x, y = _xy
            return x * y

    m = MyModel.load({"y": 5})
    with pytest.raises(MarshallerRelationshipError):
        m.myrelation