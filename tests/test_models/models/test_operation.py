import pytest

from pydent import pprint
from pydent.models import Operation

@pytest.fixture(scope='function')
def op():
    op = Operation.load(
        {'created_at': '2017-11-30T16:25:49-08:00',
         'id': 133167,
         'operation_type': {'category': 'Manager',
                            'created_at': '2017-11-30T12:51:17-08:00',
                            'deployed': True,
                            'field_types': [
                                {'allowable_field_types': [{'created_at': '2017-11-30T12:51:17-08:00',
                                                            'field_type_id': 9070,
                                                            'id': 4094,
                                                            'object_type_id': 484,
                                                            'sample_type_id': 15,
                                                            'updated_at': '2017-11-30T12:51:17-08:00'}],
                                 'array': None,
                                 'choices': None,
                                 'created_at': '2017-11-30T12:51:17-08:00',
                                 'ftype': 'sample',
                                 'id': 9070,
                                 'name': 'Glycerol',
                                 'parent_class': 'OperationType',
                                 'parent_id': 1077,
                                 'part': None,
                                 'preferred_field_type_id': None,
                                 'preferred_operation_type_id': None,
                                 'required': None,
                                 'role': 'output',
                                 'routing': 'g',
                                 'sample_type': None,
                                 'updated_at': '2017-11-30T13:34:59-08:00'}
                            ],
                            'id': 1077,
                            'name': 'Make Suspension Media for Comp Cell Batch',
                            'on_the_fly': None,
                            'updated_at': '2017-11-30T12:52:18-08:00'},
         'operation_type_id': 1077,
         'field_values': [{'allowable_field_type_id': 4094,
                            'child_item_id': None,
                            'child_sample_id': 11838,
                            'column': None,
                            'created_at': '2017-11-30T16:25:49-08:00',
                            'field_type_id': 9070,
                            'id': 519830,
                            'name': 'Glycerol',
                            'parent_class': 'Operation',
                            'parent_id': 133167,
                            'role': 'output',
                            'row': None,
                            'updated_at': '2017-11-30T16:25:49-08:00',
                            'value': None,
                           'field_type': {'array': False}},
                           {'allowable_field_type_id': 4097,
                            'child_item_id': None,
                            'child_sample_id': 11839,
                            'column': None,
                            'created_at': '2017-11-30T16:25:49-08:00',
                            'field_type_id': 9073,
                            'id': 519831,
                            'name': 'Water',
                            'parent_class': 'Operation',
                            'parent_id': 133167,
                            'role': 'output',
                            'row': None,
                            'updated_at': '2017-11-30T16:25:49-08:00',
                            'value': None,
                            'field_type': {'array': False}}],
         'parent_id': 3,
         'status': 'planning',
         'updated_at': '2017-11-30T16:25:49-08:00',
         'user_id': 193,
         'x': 368.0,
         'y': 192.0})
    return op

def test_field_value(op):

    fv = op.field_value("Water", "input")
    assert fv == 519831

def test_operation(op):
    op.init_field_values()
    print(op.field_values)
