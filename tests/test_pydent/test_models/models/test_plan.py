from pydent.models import (FieldValue, Operation, Plan)


def test_plan_constructor(fake_session):
    g = fake_session.Plan.new()
    assert g.name is not None
    print(g.plan_associations)
    assert g.operations is None
    assert g.wires == []

    g = Plan(name="MyPlan", status='running')
    assert g.name == 'MyPlan'
    assert g.status == 'running'


def test_add_operation(fake_session):
    op = fake_session.Operation.load({"id": 4})
    p = fake_session.Plan.new()

    # add first operation
    assert p.operations is None
    p.add_operation(op)
    assert p.operations == [op]

    # add second operation
    op2 = fake_session.Operation.load({'id': 5})
    p.add_operation(op2)
    assert p.operations == [op, op2]


def test_add_operations(fake_session):
    op = fake_session.Operation.load({"id": 4})
    op2 = fake_session.Operation.load({'id': 5})
    ops = [op, op2]
    p = fake_session.Plan.new()
    p.add_operations(ops)
    assert p.operations == [op, op2]


def test_wire(fake_session):
    p = fake_session.Plan.new()
    src = fake_session.FieldValue.load({'name': 'myinput'})
    dest = fake_session.FieldValue.load({'name': 'myoutput'})
    p.wire(src, dest)
    assert len(p.wires) == 1
    assert p.wires[0].source.name == 'myinput'
    assert p.wires[0].destination.name == 'myoutput'
    print(p.wires)


# def test_est_costs(session):
#    p = session.Plan.find(79147)
#    assert p, "Plan 79147 not found"
#    cost = p.estimate_cost()
#    print(cost)


def test_add_wire(fake_session):

    p = fake_session.Plan.new()
    assert p.wires == []
    fv1 = fake_session.FieldValue.new(name="input")
    fv2 = fake_session.FieldValue.new(name="output")
    p.wire(fv1, fv2)
    assert len(p.wires) == 1


def test_count_wires(example_plan):
    """Test whether the wire collection collects the appropriate number of wires"""
    assert len(example_plan.wires) == 80, "There should be exactly 80 wires in this plan."


# TODO: make this a deterministic test
"""def test_new_plan(session):

    p = fake_session.Plan.new()
    p.connect_to_session(session)
    assert p.operations is None
    assert p.plan_associations is None

    p.id = 1000000
    assert p.operations == []
    assert p.plan_associations == []"""


# def test_submit(session):
#     primer = session.SampleType.find(1).samples[-1]
#
#     # get Order Primer operation type
#     ot = session.OperationType.find(328)
#
#     # create an operation
#     order_primer = ot.instance()
#
#     # set io
#     order_primer.set_output("Primer", sample=primer)
#     order_primer.set_input("Urgent?", value="no")
#
#     # create a new plan and add operations
#     p = session.Plan(name="MyPlan")
#     p.add_operation(order_primer)
#
#     # save the plan
#     p.create()
#
#     # estimate the cost
#     p.estimate_cost()
#
#     # show the plan
#     p.show()
#
#     # submit the plan
#     p.submit(session.current_user, session.current_user.budgets[0])

# def test_submit_pcr(session):
#     def get_op(name):
#         return session.OperationType.where(
#               {'name': name, 'deployed': True})[-1].instance()
#
#     make_pcr_fragment = get_op('Make PCR Fragment')
#     pour_gel = get_op('Pour Gel')
#     run_gel = get_op('Run Gel')
#     extract_gel_slice = get_op('Extract Gel Slice')
#     purify_gel = get_op('Purify Gel Slice')
#
#     # setup pcr
#     make_pcr_fragment.set_input('Forward Primer',
#                                 item=session.Item.find(81867))
#     make_pcr_fragment.set_input('Reverse Primer',
#                                 item=session.Item.find(57949))
#     make_pcr_fragment.set_input('Template', item=session.Item.find(61832))
#     make_pcr_fragment.set_output('Fragment',
#                                  sample=session.Sample.find(16976))
#
#     # setup outputs
#     # run_gel.set_output(sample=session.Sample.find(16976))
#     # extract_gel_slice.set_output(sample=session.Sample.find(16976))
#     # purify_gel.set_output(sample=session.Sample.find(16976))
#     # purify_gel.pour_gel(sample=session.Sample.find(16976))
#
#     # new plan
#     p = session.fake_session.Plan.new()
#     p.add_operations([make_pcr_fragment, pour_gel, run_gel,
#                       extract_gel_slice, purify_gel])
#
#     p.add_wires([
#         (make_pcr_fragment.output("Fragment"), run_gel.input("Fragment")),
#         (pour_gel.output("Lane"), run_gel.input("Gel")),
#         (run_gel.output("Fragment"), extract_gel_slice.input("Fragment")),
#         (extract_gel_slice.output("Fragment"), purify_gel.input("Gel"))
#     ])
#
#     make_pcr_fragment.set_output("Fragment",
#                                  sample=session.Sample.find(16976))
#
#
#     pdata = p.to_save_json()
#
#     # wire up the operations
#     # p.wire(make_pcr_fragment.outputs[0], run_gel.input('Fragment'))
#     # p.wire(pour_gel.outputs[0], run_gel.input('Gel'))
#     # p.wire(run_gel.outputs[0], extract_gel_slice.input('Fragment'))
#     # p.wire(extract_gel_slice.outputs[0], purify_gel.input('Gel'))
#
#     # save the plan
#     p.create()
#
#     # estimate the cost
#     p.estimate_cost()
#
#     p.validate()
#
#     # show the plan
#     p.show()
#
#     # submit the plan
#     p.submit(session.current_user, session.current_user.budgets[0])


# # TODO: having difficulty patching plans/operations here...
# def test_replan(session):
#
#     p = session.Plan.find(79797)
#     newplan = p.replan()
#     newplan.print()
#
#     for op in newplan.operations:
#         if op.operation_type.name == "Make PCR Fragment":
#             op.set_input('Template', item=session.Item.find(57124))
#             newplan.patch(newplan.to_save_json())
