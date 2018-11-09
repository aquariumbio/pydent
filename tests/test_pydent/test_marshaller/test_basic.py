import pytest

from pydent.marshaller import add_schema, fields


# TESTING SCHEMA

@pytest.fixture(scope="module")
def mymodel():
    @add_schema
    class MyModel(object):
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

        def __init__(self):
            pass

    return MyModel


def test_basic_field_access(mymodel):
    """
    Fields in the model definition should be accumulated in the 'include'
    attribute of its schema.
    """
    # Test basic access

    assert hasattr(mymodel, MODEL_SCHEMA)
    assert hasattr(getattr(mymodel, MODEL_SCHEMA), META)

    schema = getattr(mymodel, MODEL_SCHEMA)
    meta = getattr(schema, META)

    # field3 should be inherited from the "include" dictionary in Fields
    assert "field3" in meta.include

    # field4 should be inherited from class variable located in Fields
    assert "field4" in meta.include

    # field5 (a Relation, a subclass of fields.Field) should also be present
    assert "field5" in meta.include

    # other attributes should not be inherited
    assert "something" not in meta.include
