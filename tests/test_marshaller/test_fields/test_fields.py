import json

import pytest

from pydent.marshaller.base import add_schema
from pydent.marshaller.fields import Callback
from pydent.marshaller.fields import Field
from pydent.marshaller.fields import Nested
from pydent.marshaller.fields import Relationship


def test_default(base):
    @add_schema
    class Author(base):
        fields = dict(field=Field(default=5))

    a = Author()
    assert a.field == 5
    a.field = 6
    assert a.field == 6
    del a.field
    assert a.field == 5

    a2 = Author(dict(field=6))
    assert a2.field == 6


@pytest.mark.parametrize("field", ["field", "callback", "nested", "relationship"])
def test_allow_none_default(base, field):
    @add_schema
    class Publisher(base):
        pass

    @add_schema
    class Author(base):
        fields = dict(
            field=Field(),
            callback=Callback("find"),
            nested=Nested("Publisher"),
            relationship=Relationship("Publisher", "where"),
        )

        def find(self):
            pass

        def where(self, model_name):
            pass

    setattr(Author(), field, None)
    # Author.set_data({field: None})
    assert True


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


@pytest.mark.parametrize(
    "init",
    [
        pytest.param(lambda k, data: k(data), id="__init__"),
        pytest.param(lambda k, data: k.load(data), id="load"),
    ],
)
@pytest.mark.parametrize(
    "ignore", [(()), (("f1")), (("f2")), (("f4")), (("f1", "f2")), (("f1", "f2", "f3"))]
)
def test_ignore(ignore, init, base):
    @add_schema
    class Model(base):
        fields = dict(f1=Field(), f2=Field(), f3=Field(), ignore=ignore)

    data = {"f1": 1, "f2": 2, "f3": 3}
    expected = dict(data)

    if isinstance(ignore, str):
        ignore = (ignore,)

    assert isinstance(Model.model_schema.ignore, tuple)
    assert set(Model.model_schema.ignore) == set(ignore)

    for i in Model.model_schema.ignore:
        expected.pop(i, None)

    m = init(Model, data)

    for i in ignore:
        assert not hasattr(m, i)
        assert i not in m.dump()
    for e in expected:
        assert hasattr(m, e), "Should have attribute {}".format(e)
        assert e in m.dump(), "Should have attribute {}".format(e)
        assert getattr(m, e) == expected[e]
        assert m.dump()[e] == expected[e]
