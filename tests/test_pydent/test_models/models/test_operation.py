import pytest

from pydent.models import Operation
from pydent.utils import pprint


@pytest.fixture(scope="module")
def generate_fake_op_data(session):
    op = session.Operation.find(133167)
    op_data = op.dump(relations=("operation_type", "field_values"))
    field_types = op.operation_type.field_types.dump(
        relations=("allowable_field_types",)
    )
    op_data["operation_type"]["field_types"] = field_types
    op_data["field_values"] = op.field_values.dump(relations=("field_type",), depth=2)

    pprint(op_data)


@pytest.fixture(scope="function")
def fake_op(fake_session):
    """(huge) fixture for making a fake operation."""
    fake_op_data = {
        "created_at": "2017-11-30T16:25:49-08:00",
        "field_values": [
            {
                "allowable_field_type_id": 4094,
                "child_item_id": None,
                "child_sample_id": 11838,
                "column": None,
                "created_at": "2017-11-30T16:25:49-08:00",
                "field_type": {
                    "allowable_field_types": [
                        {
                            "created_at": "2017-11-30T12:51:17-08:00",
                            "field_type_id": 9070,
                            "id": 4094,
                            "object_type_id": 484,
                            "sample_type_id": 15,
                            "updated_at": "2017-11-30T12:51:17-08:00",
                        }
                    ],
                    "array": None,
                    "choices": None,
                    "created_at": "2017-11-30T12:51:17-08:00",
                    "ftype": "sample",
                    "id": 9070,
                    "name": "Glycerol",
                    "operation_type": {
                        "category": "Manager",
                        "created_at": "2017-11-30T12:51:17-08:00",
                        "deployed": True,
                        "id": 1077,
                        "name": "Make Suspension " "Media for Comp " "Cell Batch",
                        "on_the_fly": None,
                        "updated_at": "2017-11-30T12:52:18-08:00",
                    },
                    "parent_class": "OperationType",
                    "parent_id": 1077,
                    "part": None,
                    "preferred_field_type_id": None,
                    "preferred_operation_type_id": None,
                    "required": None,
                    "role": "output",
                    "routing": "g",
                    "sample_type": None,
                    "updated_at": "2017-11-30T13:34:59-08:00",
                },
                "field_type_id": 9070,
                "id": 519830,
                "name": "Glycerol",
                "parent_class": "Operation",
                "parent_id": 133167,
                "role": "output",
                "row": None,
                "updated_at": "2017-11-30T16:25:49-08:00",
                "value": None,
            },
            {
                "allowable_field_type_id": 4097,
                "child_item_id": None,
                "child_sample_id": 11839,
                "column": None,
                "created_at": "2017-11-30T16:25:49-08:00",
                "field_type": {
                    "allowable_field_types": [
                        {
                            "created_at": "2017-11-30T13:33:25-08:00",
                            "field_type_id": 9073,
                            "id": 4097,
                            "object_type_id": 485,
                            "sample_type_id": 15,
                            "updated_at": "2017-11-30T13:33:25-08:00",
                        }
                    ],
                    "array": None,
                    "choices": None,
                    "created_at": "2017-11-30T13:33:25-08:00",
                    "ftype": "sample",
                    "id": 9073,
                    "name": "Water",
                    "operation_type": {
                        "category": "Manager",
                        "created_at": "2017-11-30T12:51:17-08:00",
                        "deployed": True,
                        "id": 1077,
                        "name": "Make Suspension " "Media for Comp " "Cell Batch",
                        "on_the_fly": None,
                        "updated_at": "2017-11-30T12:52:18-08:00",
                    },
                    "parent_class": "OperationType",
                    "parent_id": 1077,
                    "part": None,
                    "preferred_field_type_id": None,
                    "preferred_operation_type_id": None,
                    "required": None,
                    "role": "output",
                    "routing": "w",
                    "sample_type": None,
                    "updated_at": "2017-11-30T13:34:59-08:00",
                },
                "field_type_id": 9073,
                "id": 519831,
                "name": "Water",
                "parent_class": "Operation",
                "parent_id": 133167,
                "role": "output",
                "row": None,
                "updated_at": "2017-11-30T16:25:49-08:00",
                "value": None,
            },
        ],
        "id": 133167,
        "operation_type": {
            "category": "Manager",
            "created_at": "2017-11-30T12:51:17-08:00",
            "deployed": True,
            "field_types": [
                {
                    "allowable_field_types": [
                        {
                            "created_at": "2017-11-30T12:51:17-08:00",
                            "field_type_id": 9070,
                            "id": 4094,
                            "object_type_id": 484,
                            "sample_type_id": 15,
                            "updated_at": "2017-11-30T12:51:17-08:00",
                        }
                    ],
                    "array": None,
                    "choices": None,
                    "created_at": "2017-11-30T12:51:17-08:00",
                    "ftype": "sample",
                    "id": 9070,
                    "name": "Glycerol",
                    "parent_class": "OperationType",
                    "parent_id": 1077,
                    "part": None,
                    "preferred_field_type_id": None,
                    "preferred_operation_type_id": None,
                    "required": None,
                    "role": "output",
                    "routing": "g",
                    "updated_at": "2017-11-30T13:34:59-08:00",
                },
                {
                    "allowable_field_types": [
                        {
                            "created_at": "2017-11-30T13:33:25-08:00",
                            "field_type_id": 9073,
                            "id": 4097,
                            "object_type_id": 485,
                            "sample_type_id": 15,
                            "updated_at": "2017-11-30T13:33:25-08:00",
                        }
                    ],
                    "array": None,
                    "choices": None,
                    "created_at": "2017-11-30T13:33:25-08:00",
                    "ftype": "sample",
                    "id": 9073,
                    "name": "Water",
                    "parent_class": "OperationType",
                    "parent_id": 1077,
                    "part": None,
                    "preferred_field_type_id": None,
                    "preferred_operation_type_id": None,
                    "required": None,
                    "role": "output",
                    "routing": "w",
                    "updated_at": "2017-11-30T13:34:59-08:00",
                },
            ],
            "id": 1077,
            "name": "Make Suspension Media for Comp Cell Batch",
            "on_the_fly": None,
            "updated_at": "2017-11-30T12:52:18-08:00",
        },
        "operation_type_id": 1077,
        "parent_id": 3,
        "status": "planning",
        "updated_at": "2017-11-30T16:25:49-08:00",
        "user_id": 193,
        "x": 368.0,
        "y": 192.0,
    }

    return fake_session.Operation.load(fake_op_data)


def test_constructor(fake_session):

    op = fake_session.Operation.new()
    op_dump = op.dump()
    assert op_dump["routing"] == {}
    assert "x" in op_dump
    assert "y" in op_dump


def test_outputs(fake_session):
    op = fake_session.Operation.load(
        {
            "field_values": [
                {"role": "output"},
                {"role": "output"},
                {"role": "output"},
                {"role": "input"},
            ]
        }
    )
    assert op.outputs == op.field_values[:-1]
    assert len(op.outputs) == 3


def test_inputs(fake_session):
    op = fake_session.Operation.load(
        {
            "field_values": [
                {"role": "input"},
                {"role": "input"},
                {"role": "input"},
                {"role": "output"},
            ]
        }
    )
    assert len(op.inputs) == 3
    assert op.inputs == op.field_values[:-1]


def test_field_value(fake_op):
    fv = fake_op.field_value("Glycerol", "output")
    assert fv.id == 519830


def test_operation_init_fieldvalues(fake_op):
    """Test initializing of field_values for operation."""

    # remove field_values
    fake_op.field_values = None
    assert fake_op.field_values is None

    # initialize field_values
    fake_op.init_field_values()
    assert len(fake_op.field_values) == len(fake_op.operation_type.field_types) == 2


def test_operation_copy(fake_op):

    for fv in fake_op.field_values:
        assert fv.id is not None
        assert fv.child_sample_id

    for fv in fake_op.copy().field_values:
        assert fv.id is None
        assert fv.child_sample_id


def test_operation_copy_does_not_anonymize_items(fake_op, fake_session):

    for fv in fake_op.field_values:
        fv.item = fake_session.Item.load({"id": 123})
        assert fv.child_item_id

    for fv in fake_op.field_values:
        assert fv.id is not None
        assert fv.child_sample_id
        assert fv.child_item_id
        assert fv.parent_id
        assert fv.item

    for fv in fake_op.copy().field_values:
        assert fv.id is None
        assert fv.parent_id is None
        assert fv.child_sample_id
        assert fv.child_item_id
        assert fv.item
