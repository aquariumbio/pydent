import pytest
from pydent.models import *


def test_plan_constructor():

    g = Plan()
    assert g.name is None
    assert g.source is None
    assert g.destination is None
    assert g.status == 'planning'
    print(g.plan_associations)
    assert g.operations == None
    assert g.wires == None

    g = Plan(name="MyPlan", status='running')
    assert g.name == 'MyPlan'
    assert g.status == 'running'


def test_add_operation(fake_session):

    op = Operation.load({"id": 4})
    p = Plan()

    # add first operation
    assert p.operations == None
    p.add_operation(op)
    assert p.operations == [op]

    # add second operation
    op2 = Operation.load({'id': 5})
    p.add_operation(op2)
    assert p.operations == [op, op2]


def test_add_operations():

    op = Operation.load({"id": 4})
    op2 = Operation.load({'id': 5})
    ops = [op, op2]
    p = Plan()
    p.add_operations(ops)
    assert p.operations == [op, op2]


def test_wire():
    p = Plan()
    src = FieldValue.load({'name': 'myinput'})
    dest = FieldValue.load({'name': 'myoutput'})
    p.wire(src, dest)
    assert len(p.wires) == 1
    assert p.wires[0].source.name == 'myinput'
    assert p.wires[0].destination.name == 'myoutput'
    print(p.wires)


def test_est_costs(session):
    p = session.Plan.find(79147)
    cost = p.estimate_cost()
    print(cost)


def test_to_save_json(session):

    p = session.Plan.find(79147)
    from pydent import pprint

    pprint(p.to_save_json())


def test_submit(session):
    primer = session.Sample.find(17042)
    # ly_primer = session.ObjectType.find_by_name("Lyophilized Primer")
    # primer_aliquot = session.ObjectType.find_by_name("Primer Aliquot")
    # primer_stock = session.ObjectType.find_by_name("Primer Stock")
    ot = session.OperationType.find_by_name("Order Primer")
    order_primer = session.OperationType.find_by_name("Order Primer").instance()
    print(ot.field_types.name)
    order_primer.set_output("Primer", sample=primer)

    p = session.Plan(name="MyPlan")
    p.add_operation(order_primer)
    ops = p.operations
    print(p)
    print(p.operations[0].field_values)
    print(p.to_save_json())
    p.validate()
    p.save()

def test_save(session):
    from pydent import pprint
    p = session.Plan.find(79147)
    operations = p.operations
    p.id = None
    p.operations = operations
    # # pprint(p.dump(relations={'operations': ['field_values'], 'wires': ['source', 'destination']}))
    # p.id = None
    p.save()