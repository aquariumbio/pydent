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


def test_json_deserialize_with_empty_string():
    class MySchema(Schema):
        json = JSON()

    myschema = MySchema()
    d = myschema.load({'json': ''})
    assert d.data['json'] is None
    assert len(d.errors) == 0

def test_json_deserialize_with_strict():
    class MySchema(Schema):
        json = JSON(allow_none=True)

    myschema = MySchema()
    d = myschema.load({'json': 'this is not a JSON'})
    assert len(d.errors) == 1

def test_json_deserialize_without_strict():
    class MySchema(Schema):
        json = JSON(allow_none=True, strict=False)

    myschema = MySchema()
    d = myschema.load({'json': 'this is not a JSON'})
    assert len(d.errors) == 0
    assert d.data['json'] == 'this is not a JSON'


def test_json_deserialize_with_None():
    class MySchema(Schema):
        json = JSON(allow_none=True)

    myschema = MySchema()
    d = myschema.load({'json': None})
    assert d.data['json'] is None
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