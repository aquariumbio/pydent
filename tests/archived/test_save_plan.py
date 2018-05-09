from pydent import models
from marshmallow import pprint


def test_submit_order_primer(session):
    order_primer = session.OperationType.where(
        {"deployed": True, "name": "Assemble Plasmid"})[0]

    order_primer_op = order_primer.instance()

    p = models.Plan(name="MyOrderPrimerTest")
    p.add_operation(order_primer_op)
    p.connect_to_session(session)
    # p.add_operation(order_primer_op)

    p.create()


def test_plan_with_parameter(session):
    primer = session.SampleType.find_by_name('Primer')
    assert(primer), "Sample type Primer not found"
    print("primer:\n{}\n".format(primer))

    # get Order Primer operation type
    ot = session.OperationType.find_by_name('Order Primer')
    assert ot, "Operation type Order Primer not found"
    print("op type:\n{}\n".format(ot))

    # create an operation
    order_primer = ot.instance()

    # set io
    order_primer.set_output("Primer", sample=primer.samples[0])
    order_primer.set_input("Urgent?", value="no")

    # create a new plan
    p = models.Plan(name="MyPlan")

    # connect the plan to the session
    p.connect_to_session(session)

    # add the operation to the plan
    p.add_operation(order_primer)

    pprint(p.to_save_json())

    # save the plan
    p.create()

    assert p.id is not None
    plan_from_server = session.Plan.find(p.id)
    assert len(plan_from_server.operations) == 1


def test_parameter_to_zero(session):
    test_plan = models.Plan(name="Test Plan")
    op_type = session.OperationType.find_by_name('Challenge and Label')
    assert(op_type), "Operation type Challenge and Label not found"

    op1 = op_type.instance()
    op1.set_input('Protease Concentration', value=0)

    op2 = op_type.instance()
    op2.set_input('Protease Concentration', value=250)

    test_plan.add_operations([op1, op2])

    assert op1.input('Protease Concentration').value == 0
    assert op2.input('Protease Concentration').value == 250
    assert not op1.input('Protease Concentration').value == 2

    # test_plan.connect_to_session(session)
    # test_plan.create()


def test_submit_gibson(session):

    # find "Assembly Plasmid" protocol
    op_types = session.OperationType.where(
        {"deployed": True, "name": "Assemble Plasmid"})
    assert(len(op_types) > 0), "Operation type Assemble Plasmid not found"
    gibson_type = op_types[0]

    # instantiate gibson operation
    gibson_op = gibson_type.instance()
    gibson_op.field_values = []

    # set output
    gibson_op.set_output(
        "Assembled Plasmid",
        sample=session.Sample.find_by_name("pCAG-NLS-HA-Bxb1"))

    # set input 1
    gibson_op.add_to_input_array("Fragment",
                                 sample=session.Sample.find_by_name(
                                     "SV40NLS1-FLP-SV40NLS2"),
                                 item=session.Item.find(84034))

    # set input 2
    gibson_op.add_to_input_array("Fragment",
                                 sample=session.Sample.find_by_name(
                                     "CRPos0-HDAC4_split"),
                                 item=session.Item.find(83714))

    # set input 3
    sample = session.Sample.find_by_name("_HDAC4_split_part1")
    fv = gibson_op.add_to_input_array("Fragment",
                                      sample=sample)

    # PCR
    pcr_type = session.OperationType.where(
        {"deployed": True, "name": "Make PCR Fragment"})[0]
    pcr_op = pcr_type.instance()
    pcr_op.set_input("Forward Primer", sample=sample.field_value(
        "Forward Primer").sample)
    pcr_op.set_input("Reverse Primer", sample=sample.field_value(
        "Forward Primer").sample)
    pcr_op.set_input("Template", sample=sample.field_value("Template").sample)
    pcr_op.set_output("Fragment", sample=sample)

    # Run gel
    gel_type = session.OperationType.where(
        {"deployed": True, "name": "Run Gel"})[0]
    gel_op = gel_type.instance()
    gel_op.set_input("Fragment", sample=sample)
    gel_op.set_output("Fragment", sample=sample)

    # extract gel
    extract_type = session.OperationType.where(
        {"deployed": True, "name": "Extract Gel Slice"})[0]
    extract_op = extract_type.instance()
    extract_op.set_input("Fragment", sample=sample)
    extract_op.set_output("Fragment", sample=sample)

    # purify gel slice
    purify_type = session.OperationType.where(
        {"deployed": True, "name": "Purify Gel Slice"})[0]
    purify_op = purify_type.instance()
    purify_op.set_input("Gel", sample=sample)
    purify_op.set_output("Fragment", sample=sample)

    # create a new plan and add operations
    p = models.Plan(name="MyPlan")
    p.connect_to_session(session)
    p.add_operation(gibson_op)
    p.add_operation(pcr_op)
    p.add_operation(gel_op)
    p.add_operation(extract_op)
    p.add_operation(purify_op)

    # wires
    p.wire(purify_op.output("Fragment"), fv)

    # create the plan on the server
    p.create()

    # add some more wires
    p.wire(extract_op.output("Fragment"), purify_op.input("Gel"))
    p.wire(gel_op.output("Fragment"), extract_op.input("Fragment"))
    p.wire(pcr_op.output("Fragment"), gel_op.input("Fragment"))
    p.wire(pcr_op.output("Fragment"), gel_op.input("Fragment"))

    # save the plan
    p.save()

    # print("You may open you plan here: {}".format(
    #       session.url + "/plans?plan_id={}".format(p.id)))
