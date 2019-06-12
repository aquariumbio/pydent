import pytest

from pydent.marshaller.base import add_schema
from pydent.marshaller.fields import Field


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
