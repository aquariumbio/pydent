from pydent.marshaller.base import add_schema
from pydent.marshaller.fields import Field


def test_marshalling_accessor(base):
    class Int(Field):
        def serialize(self, obj, val):
            return int(val)

        def deserialize(self, obj, val):
            return str(val)

    @add_schema
    class MyModel(base):
        fields = dict(field=Field(), id=Int())

    model = MyModel()
    model.field = 4
    model.id = 50
    print(model.field)
    assert type(model.id) is str
    assert model._get_data()["id"] is 50
