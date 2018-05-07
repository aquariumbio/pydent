from pydent.marshaller.field_extensions import JSON
from marshmallow import Schema
import json


def test_json_deserialize():
    class MySchema(Schema):
        json = JSON()

    myschema = MySchema()
    d = myschema.load({'json': json.dumps({'name': 'Justin'})})
    assert d.data['json'] == {'name': 'Justin'}
    assert len(d.errors) == 0


def test_json_deserialize_with_error():
    class MySchema(Schema):
        json = JSON()

    myschema = MySchema()
    d = myschema.load({'json': 'not a json'})
    assert len(d.errors) == 1


def test_json_serialize():
    class MySchema(Schema):
        json = JSON()

    class MyModel:
        pass

    m = MyModel()
    m.json = {'name': 'model'}

    schema = MySchema()
    d = schema.dump(m)
    assert d.data['json'] == json.dumps(m.json)
    assert len(d.errors) == 0


def test_json_serialize_with_error():
    class MySchema(Schema):
        json = JSON()

    class MyModel:
        pass

    m = MyModel()
    m.json = MySchema
    schema = MySchema()
    d = schema.dump(m)
    assert len(d.errors) == 1
