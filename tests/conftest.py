import functools

import pytest

from pydent.marshaller import SchemaModel
from pydent.marshaller.registry import ModelRegistry
from pydent.marshaller.registry import SchemaRegistry


def pytest_configure(config):
    # register an additional marker
    config.addinivalue_line(
        "markers", "recordmode(mode): mark test to have its requests recorded"
    )


def pytest_addoption(parser):
    parser.addoption(
        "--webtest", action="store_true", default=False, help="run web tests"
    )
    parser.addoption(
        "--recordmode",
        action="store",
        default="no",
        help="[no, all, new_episodes, once, none]",
    )


def pytest_collection_modifyitems(config, items):
    skip_web = pytest.mark.skip(reason="need --webtest option to run")
    record_mode = pytest.mark.record(config.getoption("--recordmode"))
    for item in items:
        if config.getoption("--recordmode") != "no":
            item.add_marker(record_mode)
        if "webtest" in item.keywords:
            if not config.getoption("--webtest"):
                item.add_marker(skip_web)


@pytest.fixture(autouse=True)
def rollback_registries():
    """Rollback registries so that any newly created classes will not persist
    while testing."""
    old_schemas = dict(SchemaRegistry.schemas)
    old_models = dict(ModelRegistry.models)
    yield
    SchemaRegistry.schemas = old_schemas
    ModelRegistry.models = old_models


@pytest.fixture(autouse=True)
def replace_dir(monkeypatch):
    """Monkey_patches the __dir__ function so that the python debugger does not
    step through the __getattr__ methods of the field descriptors."""
    dir_func = functools.partial(SchemaModel.__dir__)

    def __dir__(self):
        attrs = dir_func(self)
        for f in self.model_schema.fields:
            if f in attrs:
                attrs.remove(f)
        return list(attrs)

    monkeypatch.setattr(SchemaModel, "__dir__", __dir__)
