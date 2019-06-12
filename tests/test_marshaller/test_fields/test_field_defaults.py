import pytest

from pydent.marshaller.base import add_schema
from pydent.marshaller.fields import Field, Callback, Relationship, Nested


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
