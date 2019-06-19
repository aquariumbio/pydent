from pydent.marshaller.base import add_schema
from pydent.marshaller.fields import Field
import json


class JSON(Field):
    def _deserialize(self, owner, data):
        return json.loads(data)

    def _serialize(self, owner, data):
        return json.dumps(data)


def test_JSON_example(base):
    @add_schema
    class MyModel(base):
        fields = dict(field=JSON())

    m1 = MyModel.load({"field": json.dumps({"id": 5, "name": "m1"})})
    m2 = MyModel({"field": json.dumps({"id": 7, "name": "m2"})})

    assert m1.field == {"id": 5, "name": "m1"}
    assert m1.dump() == {"field": json.dumps({"id": 5, "name": "m1"})}
    assert m2.field == {"id": 7, "name": "m2"}
    assert m2.dump() == {"field": json.dumps({"id": 7, "name": "m2"})}
