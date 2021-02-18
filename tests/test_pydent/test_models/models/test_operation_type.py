import pytest

from pydent.models import OperationType

# def test_operation_type_codes(session):
#     ot = session.OperationType.find(1065)
#     ot.codes
#
#
# def test_operation_type_ops(session):
#     ot = session.OperationType.find(1065)
#     ot.operations


def test_operation_type_field_type(fake_session):
    """Test field_type(name, role) method."""
    fake_ot = fake_session.OperationType.load(
        {
            "category": "Yeast Display",
            "created_at": "2017-11-20T15:04:20-08:00",
            "deployed": True,
            "field_types": [
                {
                    "array": None,
                    "choices": None,
                    "created_at": "2017-11-20T15:08:58-08:00",
                    "ftype": "sample",
                    "id": 8840,
                    "name": "96 well plate",
                    "parent_class": "OperationType",
                    "parent_id": 1065,
                    "part": None,
                    "preferred_field_type_id": None,
                    "preferred_operation_type_id": None,
                    "required": None,
                    "role": "output",
                    "routing": None,
                    "updated_at": "2017-11-20T15:17:40-08:00",
                },
                {
                    "array": True,
                    "choices": None,
                    "created_at": "2017-11-20T15:08:58-08:00",
                    "ftype": "sample",
                    "id": 8841,
                    "name": "Labeled Yeast Library",
                    "parent_class": "OperationType",
                    "parent_id": 1065,
                    "part": None,
                    "preferred_field_type_id": None,
                    "preferred_operation_type_id": None,
                    "required": None,
                    "role": "input",
                    "routing": "YL",
                    "updated_at": "2017-11-24T09:53:06-08:00",
                },
            ],
            "id": 1065,
            "name": "Transfer to 96 Well Plate",
            "on_the_fly": None,
            "updated_at": "2017-11-24T10:10:49-08:00",
        }
    )

    assert fake_ot.field_type("96 well plate", "output").id == 8840
    assert fake_ot.field_type("Labeled Yeast Library", "input").id == 8841
    assert not fake_ot.field_type("Labeled Yeast Library", "output")


def test_new_operation_type(fake_session):
    sample_type = fake_session.SampleType.new(name='Fluff')
    object_type = fake_session.ObjectType.new(name='Big Tub')
    type = fake_session.AllowableFieldType(sample_type=sample_type, object_type=object_type)
    field_type = fake_session.FieldType(
        name='input_one',
        role='input',
        allowable_field_types=[type]
    )
    operation_type = fake_session.OperationType.new(
        name='dummy',
        category='testing',
        field_types=[field_type]
    )

    assert operation_type is not None
