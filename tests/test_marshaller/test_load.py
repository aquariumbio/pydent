from marshmallow import fields
from pydent.marshaller import add_schema, MarshallerBase


def test_load_all():
    """
    This test loading a model with data.
    The model is expected to collect the attributes from the
    JSON formatted data
    """

    @add_schema
    class MyModel(MarshallerBase):
        fields = dict(
            field4=fields.Field(),
            field5=fields.Field(),
            something=5,
            additional=("field1", "field2"),
            include={
                "field3": fields.Field(),
                "field6": fields.Field()
            }
        )

    u = MyModel.load({"id": 5, "name": "Jill"})

    assert u.id == 5
    assert u.name == "Jill"


def test_no_load_all():
    """
    Test loading a model without loading missing values.
    The model is expected to NOT collect
    the attributes from the JSON formatted data
    """

    @add_schema
    class MyModel(MarshallerBase):
        fields = dict(
            load_all=False,
            field4=fields.Field(),
            field5=fields.Field(),
            something=5,
            additional=("field1", "field2"),
            include={
                "field3": fields.Field(),
                "field6": fields.Field()
            }
        )

    u = MyModel.load({"id": 5, "name": "Jill"})

    assert not hasattr(u, "id")
    assert not hasattr(u, "name")


def test_ignore():
    """Test loading a model with ignored fields.
    The model is expected to NOT have an id or field1, but have a name
    """

    @add_schema
    class MyModel(MarshallerBase):
        fields = dict(
            load_all=True,
            field4=fields.Field(),
            field5=fields.Field(),
            something=5,
            additional=("field1", "field2"),
            include={
                "field3": fields.Field(),
                "field6": fields.Field()
            },
            ignore=("id", "field1")
        )

    u = MyModel.load({"id": 5, "name": "Jill", "field1": 1})

    assert not hasattr(u, "id")
    assert not hasattr(u, "field1")
    assert u.name == "Jill"
