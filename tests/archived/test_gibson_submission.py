from pydent import models
from pydent.exceptions import TridentRequestError


def test_submit_gibson(session):

    # find "Assembly Plasmid" protocol
    op_types = session.OperationType.where(
        {"deployed": True, "name": "Assemble Plasmid"})
    assert len(op_types) > 0, "Operation type Assemble Plasmid not found"
    gibson_type = op_types[0]

    # instantiate gibson operation
    gibson_op = gibson_type.instance()
    gibson_op.field_values = []

    # set output
    sample = session.Sample.find_by_name("pCAG-NLS-HA-Bxb1")
    assert sample, "Sample \"pCAG-NLS-HA-Bxb1\" not found"
    gibson_op.set_output(
        "Assembled Plasmid",
        sample=sample)

    # set input 1
    sample = session.Sample.find_by_name("SV40NLS1-FLP-SV40NLS2")
    assert sample, "Sample \"SV40NLS1-FLP-SV40NLS2\" not found"
    item = session.Item.find(84034)
    assert item, "Item not found"
    gibson_op.add_to_input_array(
        "Fragment",
        sample=sample,
        item=item)

    # set input 2
    sample = session.Sample.find_by_name(
        "CRPos0-HDAC4_split")
    assert sample, "Sample \"CRPos0-HDAC4_split\" not found"
    item = session.Item.find(83714)
    assert item, "Item not"
    gibson_op.add_to_input_array("Fragment",
                                 sample=sample,
                                 item=item)

    # set input 3
    sample = session.Sample.find_by_name("_HDAC4_split_part1")
    assert sample, "Sample \"_HDAC4_split_part1\" not found"
    fv = gibson_op.add_to_input_array("Fragment",
                                      sample=sample)

    # PCR
    op_types = session.OperationType.where(
        {"deployed": True, "name": "Make PCR Fragment"})
    assert len(op_types) > 0, "Operation type Make PCR Fragment not found"
    pcr_type = op_types[0]
    pcr_op = pcr_type.instance()
    forward_primer_sample = sample.field_value("Forward Primer").sample
    assert forward_primer_sample
    pcr_op.set_input("Forward Primer", sample=forward_primer_sample)
    pcr_op.set_input("Reverse Primer", sample=forward_primer_sample)
    template_sample = sample.field_value("Template").sample
    assert template_sample
    pcr_op.set_input("Template", sample=template_sample)
    pcr_op.set_output("Fragment", sample=sample)

    # Run gel
    op_types = session.OperationType.where(
        {"deployed": True, "name": "Run Gel"})
    assert len(op_types) > 0, "Operation type Run Gel not found"
    gel_type = op_types[0]
    gel_op = gel_type.instance()
    gel_op.set_input("Fragment", sample=sample)
    gel_op.set_output("Fragment", sample=sample)

    # extract gel
    op_types = session.OperationType.where(
        {"deployed": True, "name": "Extract Gel Slice"})
    assert len(op_types) > 0, "Operation type Extract Gel Slice not found"
    extract_type = op_types[0]
    extract_op = extract_type.instance()
    extract_op.set_input("Fragment", sample=sample)
    extract_op.set_output("Fragment", sample=sample)

    # purify gel slice
    op_types = session.OperationType.where(
        {"deployed": True, "name": "Purify Gel Slice"})
    assert len(op_types) > 0, "Operation type Purify Gel Slice not found"
    purify_type = op_types[0]
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
    p.wire(extract_op.output("Fragment"), purify_op.input("Gel"))
    p.wire(gel_op.output("Fragment"), extract_op.input("Fragment"))
    p.wire(pcr_op.output("Fragment"), gel_op.input("Fragment"))
    p.wire(pcr_op.output("Fragment"), gel_op.input("Fragment"))

    # create the plan on the Aq server
    try:
        p.create()
    except TridentRequestError as error:
        assert False, "plan creation failed for request:\n{}".format(error)

    # estimate the cost
    p.estimate_cost()

    # validate the plan
    p.validate()

    # show the plan
    p.show()

    # submit the plan
    p.submit(session.current_user, session.current_user.budgets[0])

    print("You may open you plan here: {}".format(
        session.url + "/plans?plan_id={}".format(p.id)))
