import pytest
import json
from pydent.planner import Planner


@pytest.fixture(scope='function')
def fake_plan(fake_session):
    with open('fromaq.json') as f:
        plan = fake_session.Plan.load(json.load(f))
    return plan


def test_fake_plan_load(fake_plan):
    assert fake_plan.operations


def test_fake_plan_copy(fake_plan):
    """Copying plans should anonymize operations and wires"""
    copied_plan = fake_plan.copy()
    assert copied_plan.operations
    for op in copied_plan.operations:
        assert op.id is None
        print(op.raw)


def test_copy_planner(fake_plan, fake_session):

    canvas = Planner(fake_session)
    canvas.plan = fake_plan
    copied = canvas.copy()

    assert not fake_plan.id is None
    assert copied.plan.id is None
    for op in copied.operations:
        assert op.id is None
        assert op.operation_type_id