import pytest
import json


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