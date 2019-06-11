import pytest
from pydent.planner import Planner

@pytest.mark.record_mode('no')
@pytest.fixture(scope='function')
def planner_example(session):
    num_chains = 4
    with session.with_cache() as sess:
        p = Planner(sess)
        for _ in range(num_chains):
            p.chain('Make PCR Fragment', 'Run Gel', 'Extract Gel Slice', 'Purify Gel Slice')
    p.plan.id = 1234
    return p


def test_add_successive_operations(session):

    p = Planner(session)
    p.create_operation_by_name("Make PCR Fragment")
    p.create_operation_by_name("Run Gel")
    assert len(p.plan.operations) == 2


def test_add_successive_operations_with_browser_session(session):

    with session.with_cache() as sess:
        p = Planner(sess)
        p.create_operation_by_name("Make PCR Fragment")
        p.create_operation_by_name("Run Gel")
    assert len(p.plan.operations) == 2


@pytest.mark.record_mode('no')
def test_copy_planner(planner_example):
    copied = planner_example.copy()
    assert planner_example.plan.id is not None
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
    assert planner_example.layout


@pytest.mark.record_mode('no')
def test_split_planner(planner_example):
    plans = planner_example.split()
    assert len(plans) == 4


@pytest.mark.record_mode('no')
def test_combine_plans(planner_example):
    plans = planner_example.split()
    combined = Planner.combine(plans)

    assert len(combined.plan.operations) == len(planner_example.plan.operations), 'number of operations should remain the same'
    assert len(combined.plan.wires) == len(planner_example.plan.wires), 'number of wires should remain the same'

