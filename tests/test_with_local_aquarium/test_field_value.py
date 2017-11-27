import pytest

from pydent import ModelRegistry
from pydent.models import *


@pytest.fixture(scope="function")
def fv_from_sample():
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
def fv_from_op():
    return {'allowable_field_type': None,
            'allowable_field_type_id': 2157,
            'child_item_id': None,
            'child_sample_id': None,
            'column': None,
            'created_at': '2016-05-09T20:41:06-07:00',
            'field_type': {'array': None,
                           'choices': None,
                           'created_at': '2017-05-08T12:44:59-07:00',
                           'ftype': 'sample',
                           'id': 2028,
                           'name': 'Ligation Product',
                           'parent_class': 'OperationType',
                           'parent_id': 384,
                           'part': False,
                           'preferred_field_type_id': 2027,
                           'preferred_operation_type_id': 383,
                           'required': None,
                           'role': 'input',
                           'routing': 'LP',
                           'updated_at': '2017-10-13T02:19:27-07:00'},
                            'allowable_field_types': [{'created_at': '2017-05-08T12:44:59-07:00',
                                       'field_type_id': 2028,
                                       'id': 2157,
                                       'object_type_id': 599,
                                       'sample_type_id': 37,
                                       'updated_at': '2017-05-08T12:44:59-07:00'}],
            'field_type_id': 2028,
            'id': 67853,
            'item': None,
            'name': 'Overhang Sequence',
            'operation': None,
            'parent_class': 'Sample',
            'parent_id': 1,
            'parent_sample': {'created_at': '2013-10-08T10:18:48-07:00',
                              'data': None,
                              'description': None,
                              'field_values': [{'allowable_field_type_id': None,
                                                'child_item_id': None,
                                                'child_sample_id': None,
                                                'column': None,
                                                'created_at': '2016-05-09T20:41:06-07:00',
                                                'field_type_id': None,
                                                'id': 67853,
                                                'name': 'Overhang Sequence',
                                                'parent_class': 'Sample',
                                                'parent_id': 1,
                                                'role': None,
                                                'row': None,
                                                'updated_at': '2016-05-09T20:41:06-07:00',
                                                'value': 'AAAAAGCAGGCTTCAAA'},
                                               {'allowable_field_type_id': None,
                                                'child_item_id': None,
                                                'child_sample_id': None,
                                                'column': None,
                                                'created_at': '2016-05-09T20:41:06-07:00',
                                                'field_type_id': None,
                                                'id': 67854,
                                                'name': 'Anneal Sequence',
                                                'parent_class': 'Sample',
                                                'parent_id': 1,
                                                'role': None,
                                                'row': None,
                                                'updated_at': '2016-05-09T20:41:06-07:00',
                                                'value': 'ATGGAAGTCACCAATGGGCTTAACCTTAAG'},
                                               {'allowable_field_type_id': None,
                                                'child_item_id': None,
                                                'child_sample_id': None,
                                                'column': None,
                                                'created_at': '2016-05-09T20:41:06-07:00',
                                                'field_type_id': None,
                                                'id': 67855,
                                                'name': 'T Anneal',
                                                'parent_class': 'Sample',
                                                'parent_id': 1,
                                                'role': None,
                                                'row': None,
                                                'updated_at': '2016-05-09T20:41:06-07:00',
                                                'value': '71.84'}],
                              'id': 1,
                              'items': [{'created_at': '2013-10-15T12:54:41-07:00',
                                         'data': None,
                                         'id': 438,
                                         'inuse': -1,
                                         'location': 'deleted',
                                         'locator_id': None,
                                         'object_type_id': 207,
                                         'quantity': -1,
                                         'sample_id': 1,
                                         'updated_at': '2014-03-04T09:52:56-08:00'},
                                        {'created_at': '2013-10-16T15:24:05-07:00',
                                         'data': None,
                                         'id': 441,
                                         'inuse': 0,
                                         'location': 'A1.100',
                                         'locator_id': None,
                                         'object_type_id': 208,
                                         'quantity': 1,
                                         'sample_id': 1,
                                         'updated_at': '2013-10-16T15:24:05-07:00'}],
                              'name': 'IAA1-Nat-F',
                              'project': 'Auxin',
                              'sample_type': {'created_at': '2013-10-08T10:18:01-07:00',
                                              'description': 'A short double stranded '
                                                             'piece of DNA for PCR and '
                                                             'sequencing',
                                              'id': 1,
                                              'name': 'Primer',
                                              'updated_at': '2015-11-29T07:55:20-08:00'},
                              'sample_type_id': 1,
                              'updated_at': '2013-10-08T10:18:48-07:00',
                              'user_id': 1},
            'role': None,
            'row': None,
            'sample': None,
            'updated_at': '2016-05-09T20:41:06-07:00',
            'value': 'AAAAAGCAGGCTTCAAA'}


@pytest.fixture(scope="function")
def item_data():
    return {'created_at': '2014-09-03T12:44:51-07:00',
            'data': '{}',
            'data_associations': None,
            'id': 10100,
            'inuse': -1,
            'location': 'deleted',
            'locator_id': None,
            'object_type': {'cleanup': 'No cleanup information',
                            'columns': None,
                            'cost': 0.01,
                            'created_at': '2014-01-06T10:37:30-08:00',
                            'data': 'No data',
                            'description': 'A Gel Lane of an agarose gel',
                            'handler': 'sample_container',
                            'id': 277,
                            'image': '',
                            'max': 500,
                            'min': 0,
                            'name': 'Gel Lane',
                            'prefix': '',
                            'release_description': '',
                            'release_method': 'query',
                            'rows': None,
                            'safety': 'No safety information',
                            'sample_type_id': 4,
                            'unit': 'Fragment',
                            'updated_at': '2014-06-24T09:52:55-07:00',
                            'vendor': 'No vendor information'},
            'object_type_id': 277,
            'quantity': -1,
            'sample': {'created_at': '2014-07-14T21:42:07-07:00',
                       'data': None,
                       'description': '',
                       'id': 1333,
                       'name': 'lux thyA cassette',
                       'project': 'biofilm-ko',
                       'sample_type_id': 4,
                       'updated_at': '2014-07-14T21:42:07-07:00',
                       'user_id': 22},
            'sample_id': 1333,
            'updated_at': '2014-09-04T11:05:06-07:00'}


def test_field_value_with_sample_parent(monkeypatch, fake_session, fv_from_sample):
    """Test the sample relationship using parent_id and parent_class"""

    def mock_find(*args):
        return Sample()

    monkeypatch.setattr(FieldValue, "find", mock_find)

    fv_from_sample["parent_class"] = "Sample"

    fv = FieldValue.load(fv_from_sample)
    fv.connect_to_session(fake_session)

    # test .operation, .parent_sample, .sample
    assert fv.operation is None
    assert fv.parent_sample is not None
    assert isinstance(fv.parent_sample, Sample)


def test_field_value_with_operation_parent(monkeypatch, fake_session, fv_from_sample):
    """Test the operation relationship using parent_id and parent_class"""

    def mock_find(*args):
        return Operation()

    monkeypatch.setattr(FieldValue, "find", mock_find)

    fv_from_sample["parent_class"] = "Operation"

    fv = FieldValue.load(fv_from_sample)
    fv.connect_to_session(fake_session)

    # test .operation, .parent_sample, .sample
    assert fv.operation is not None
    assert fv.parent_sample is None
    assert isinstance(fv.operation, Operation)


def test_field_value_relationships(monkeypatch, fake_session, fv_from_sample):
    def mock_find(self, model_name, id):
        if id is None:
            return None
        model = ModelRegistry.get_model(model_name)
        return model()

    monkeypatch.setattr(FieldValue, "find", mock_find)

    fv = FieldValue.load(fv_from_sample)
    fv.connect_to_session(fake_session)

    # has no sample, item, aft, or field_type
    assert fv.sample is None
    assert fv.item is None
    assert fv.allowable_field_type is None
    assert fv.field_type is None

    # add attributes
    fv_from_sample.update({
        "child_sample_id": 1,
        "field_type_id": 1,
        "child_item_id": 1,
        "allowable_field_type_id": 1
    })
    fv2 = FieldValue.load(fv_from_sample)
    fv2.connect_to_session(fake_session)
    print(fv2)

    # mocked request should return model instances
    # assert isinstance(fv2.sample, Sample)
    # assert isinstance(fv2.field_type, FieldType)
    # assert isinstance(fv2.item, Item)
    aft = fv2.allowable_field_type
    assert isinstance(fv2.allowable_field_type, AllowableFieldType)


def test_set_value(fake_session, fv_from_sample):
    fv = FieldValue.load(fv_from_sample)
    fv.connect_to_session(fake_session)
    fv.set_value(value=1000)
    assert fv.value == 1000


def test_set_item(fake_session, fv_from_op, item_data):
    fv = FieldValue.load(fv_from_op)
    fv.connect_to_session(fake_session)

    item = Item.load(item_data)
    item.object_type = ObjectType

    # item.connect_to_session(fake_session)

    fv.set_value(item=item)
    # assert fv.item == 1000
