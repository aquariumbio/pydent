import pytest
from pydent.base import ModelBase
from pydent.marshaller import add_schema
from pydent.marshaller import ModelRegistry, SchemaRegistry


@pytest.fixture(scope="function")
def base():
    ModelRegistry.models.pop("MyModel", None)
    SchemaRegistry.schemas.pop("MyModelSchema", None)
    yield ModelBase
    ModelRegistry.models.pop("MyModel", None)
    SchemaRegistry.schemas.pop("MyModelSchema", None)



@pytest.fixture(scope="function")
def test_model(base):
    """
    Tests heirarchical loading of a JSON file into Trident Models.

    Should return a User with name and login attributes.
    Groups attribute should contain a list of Group models.
    """

    # Make a dummy model

    # these fields should be ignored and should not appear in the model
    ignored = ("field1", "field2", "field3")

    # these fields are in the model, but should not get dumped to json
    loadonly = ("field6", "field7")

    @add_schema
    class MyModel(base):
        fields = dict(
            ignore=ignored,
            load_only=loadonly
        )

    # load the model from dummy data
    values = range(10)
    keys = ["field{}".format(x) for x in values]
    data = dict(zip(keys, values))
    m = MyModel.load(data)

    return m, ignored, loadonly, data, MyModel


def test_fields_ignored(test_model):
    m, ignored, _loadonly, data, _MyModel = test_model
    keys = list(data.keys())

    # Check model for attributes
    fields_expected_in_model = set(keys) - set(ignored)
    for field in fields_expected_in_model:
        assert hasattr(m, field)
    for field in ignored:
        assert not hasattr(m, field)


def test_fields_dumped(test_model):
    m, ignored, loadonly, data, _MyModel = test_model
    keys = list(data.keys())

    # Check dumped JSON
    fields_expected_in_dump = set(keys) - set(ignored) - set(loadonly)
    d = m.dump()
    for field in fields_expected_in_dump:
        assert field in d
    for field in ignored:
        assert field not in d


def test_load_dump_repeat(test_model):
    m, _ignored, _loadonly, data, MyModel = test_model
    keys = list(data.keys())
    assert keys

    # Check dumped JSON
    # fields_expected_in_dump = set(keys) - set(ignored) - set(loadonly)
    assert m.dump()
    m = MyModel.load(data)
    m.dump()
    m = MyModel.load(data)
