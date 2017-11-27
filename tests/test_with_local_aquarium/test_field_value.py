import pytest
from pydent import AqSession
from pydent.models import *
from pydent import ModelRegistry

@pytest.fixture(scope="function")
def fv_data():
    return {
        "field_type_id": None,
        "id": 1,
        "created_at": "2017-11-26T13:22:24-08:00",
        "child_sample_id": None,
        "parent_class": "Sample",
        "parent_id": 1,
        "row": None,
        "value": "1234.0",
        "updated_at": "2017-11-26T13:22:24-08:00",
        "column": None,
        "role": None,
        "allowable_field_type_id": None,
        "child_item_id": None,
        "name": "Length",
    }

@pytest.fixture(scope="function")
def item_data():
    return {'created_at': '2014-09-08T13:36:37-07:00',
 'data': '{}',
 'id': 10302,
 'inuse': -1,
 'location': 'deleted',
 'locator_id': None,
 'object_type_id': 350,
 'quantity': -1,
 'sample_id': 1929,
 'updated_at': '2015-07-15T11:17:04-07:00'}


def test_field_value_with_sample_parent(monkeypatch, fake_session, fv_data):
    """Test the sample relationship using parent_id and parent_class"""

    def mock_find(*args):
        return Sample()

    monkeypatch.setattr(FieldValue, "find", mock_find)

    fv_data["parent_class"] = "Sample"

    fv = FieldValue.load(fv_data)
    fv.connect_to_session(fake_session)

    # test .operation, .parent_sample, .sample
    assert fv.operation is None
    assert fv.parent_sample is not None
    assert isinstance(fv.parent_sample, Sample)


def test_field_value_with_operation_parent(monkeypatch, fake_session, fv_data):
    """Test the operation relationship using parent_id and parent_class"""

    def mock_find(*args):
        return Operation()

    monkeypatch.setattr(FieldValue, "find", mock_find)

    fv_data["parent_class"] = "Operation"

    fv = FieldValue.load(fv_data)
    fv.connect_to_session(fake_session)

    # test .operation, .parent_sample, .sample
    assert fv.operation is not None
    assert fv.parent_sample is None
    assert isinstance(fv.operation, Operation)


def test_field_value_relationships(monkeypatch, fake_session, fv_data):

    def mock_find(self, model_name, id):
        if id is None:
            return None
        model = ModelRegistry.get_model(model_name)
        return model()

    monkeypatch.setattr(FieldValue, "find", mock_find)

    fv = FieldValue.load(fv_data)
    fv.connect_to_session(fake_session)

    # has no sample, item, aft, or field_type
    assert fv.sample is None
    assert fv.item is None
    assert fv.allowable_field_type is None
    assert fv.field_type is None

    # add attributes
    fv_data.update({
        "child_sample_id": 1,
        "field_type_id": 1,
        "child_item_id": 1,
        "allowable_field_type_id": 1
    })
    fv2 = FieldValue.load(fv_data)
    fv2.connect_to_session(fake_session)
    print(fv2)

    # mocked request should return model instances
    # assert isinstance(fv2.sample, Sample)
    # assert isinstance(fv2.field_type, FieldType)
    # assert isinstance(fv2.item, Item)
    aft = fv2.allowable_field_type
    assert isinstance(fv2.allowable_field_type, AllowableFieldType)



def test_set_value(monkeypatch, fake_session, fv_data):

    fv = FieldValue.load(fv_data)
    fv.connect_to_session(fake_session)
    fv.set_value(value=1000)
    assert fv.value == 1000


def test_set_item(monkeypatch, fake_session, fv_data, item_data):

    fv = FieldValue.load(fv_data)
    fv.connect_to_session(fake_session)

    item = Item.load(item_data)
    item.object_type = ObjectType

    # item.connect_to_session(fake_session)

    fv.set_value(item=item)
    # assert fv.item == 1000
