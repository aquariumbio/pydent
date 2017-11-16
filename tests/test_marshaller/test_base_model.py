from marshmallow import fields
import pytest
from pydent.marshaller import add_schema, MarshallerBase


@pytest.fixture(scope="module")
def mymodel():

    @add_schema
    class MyModel(MarshallerBase):
        class Fields:
            field4 = fields.Field()
            field5 = fields.Field()
            something = 5
            additional = ("field1", "field2")
            include = {
                "field3": fields.Field(),
                "field6": fields.Field()
            }

        def __init__(self):
            pass
    return MyModel
