import pytest
from pydent.marshaller.schema import SchemaRegistry
from pydent.marshaller.base import SchemaModel, ModelRegistry
import functools

@pytest.fixture(scope="function")
def base():
    SchemaRegistry.schemas = {}
    ModelRegistry.models = {}

    class ModelBase(SchemaModel):
        pass

    yield ModelBase
    SchemaRegistry.schemas = {}
    ModelRegistry.models = {}


@pytest.fixture(autouse=True)
def replace_dir(monkeypatch):

    dir_func = functools.partial(SchemaModel.__dir__)

    def __dir__(self):
        attrs = dir_func(self)
        for f in self.model_schema.fields:
            if f in attrs:
                attrs.remove(f)
        return list(attrs)

    monkeypatch.setattr(SchemaModel, '__dir__', __dir__)
