import pytest
import json
from pydent.planner import Planner
import dill
import os

@pytest.fixture(scope='function')
def fake_planner(fake_session):
    here = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(here, 'fromaq.json'), 'r') as f:
        plan_json = json.load(f)

    fake_plan = fake_session.Plan.load(plan_json)
    canvas = Planner(fake_plan)
    # with open('multiplan.pkl', 'rb') as f:
    #     canvas = dill.load(f)
    # return canvas

    # fv_to_op_dict = {}
    # for op in plan.operations:
    #     for fv in op.field_values:
    #         fv_to_op_dict[fv.rid] = op
    #
    # for wire in plan.wires:
    #     assert wire.source.rid in fv_to_op_dict
    #     assert wire.destination.rid in fv_to_op_dict


def test_copy_planner(fake_planner):
    copied = fake_planner.copy()
    assert not fake_planner.plan.id is None
    assert copied.plan.id is None
    for op in copied.plan.operations:
        assert op.id is None
        assert op.operation_type_id
        assert op.field_values
        for fv in op.field_values:
            assert fv.parent_id is None
    for wire in copied.plan.wires:
        assert wire.source
        assert wire.destination
        assert wire.source.parent_id is None
        assert wire.destination.parent_id is None
    assert fake_planner.layout


# TODO: len of operations and wires remains the same
def test_split_planner(fake_planner):
    plans = fake_planner.split()
    assert len(plans) == 3


def test_combine_plans(fake_planner):
    plans = fake_planner.split()
    combined = Planner.combine(plans)

    assert len(combined.plan.operations) == len(fake_planner.plan.operations), 'number of operations should remain the same'
    assert len(combined.plan.wires) == len(fake_planner.plan.wires), 'number of wires should remain the same'

