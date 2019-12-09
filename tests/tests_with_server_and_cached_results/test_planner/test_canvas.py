import pytest

from pydent.planner import Planner
from pydent.planner import PlannerException
from pydent.planner.utils import get_subgraphs


def test_canvas_create(session):
    canvas = Planner(session)
    canvas.create()
    assert canvas.plan.id


def test_raises_exception_wiring_with_no_afts(session):
    canvas = Planner(session)
    op1 = canvas.create_operation_by_name("Make PCR Fragment", category="Cloning")
    op2 = canvas.create_operation_by_name("Check Plate", category="Cloning")

    with pytest.raises(PlannerException):
        canvas._set_wire(op1.outputs[0], op2.inputs[0])


def test_add_wire(session):
    canvas = Planner(session)
    assert len(canvas.plan.wires) == 0
    op1 = canvas.create_operation_by_name("Make PCR Fragment", category="Cloning")
    op2 = canvas.create_operation_by_name("Rehydrate Primer", category="Cloning")

    canvas.add_wire(op2.outputs[0], op1.input("Forward Primer"))
    assert len(canvas.plan.wires) == 1
    wire = canvas.plan.wires[0]
    assert (
        wire.source.allowable_field_type.sample_type_id
        == wire.destination.allowable_field_type.sample_type_id
    )
    assert (
        wire.source.allowable_field_type.object_type_id
        == wire.destination.allowable_field_type.object_type_id
    )


def test_add_wire_sets_sample_from_destination(session):
    session.set_verbose(True)
    canvas = Planner(session)
    assert len(canvas.plan.wires) == 0
    p = session.Sample.one(
        query=dict(sample_type_id=session.SampleType.find_by_name("Primer").id)
    )
    destination = canvas.create_operation_by_name(
        "Make PCR Fragment", category="Cloning"
    )
    source = canvas.create_operation_by_name("Rehydrate Primer", category="Cloning")
    canvas.set_field_value(destination.input("Forward Primer"), sample=p)
    canvas.add_wire(source.outputs[0], destination.input("Forward Primer"))
    assert source.outputs[0].sample == p


def test_add_wire_sets_sample_from_source(session):
    session.set_verbose(True)
    canvas = Planner(session)
    assert len(canvas.plan.wires) == 0
    p = session.Sample.one(
        query=dict(sample_type_id=session.SampleType.find_by_name("Primer").id)
    )
    destination = canvas.create_operation_by_name(
        "Make PCR Fragment", category="Cloning"
    )
    source = canvas.create_operation_by_name("Rehydrate Primer", category="Cloning")
    canvas.set_field_value(source.outputs[0], sample=p)
    canvas.add_wire(source.outputs[0], destination.input("Forward Primer"))
    assert destination.input("Forward Primer").sample == p


def test_collect_matching_afts(session):
    canvas = Planner(session)

    op1 = canvas.create_operation_by_name("Check Plate", category="Cloning")
    op2 = canvas.create_operation_by_name("E Coli Lysate", category="Cloning")
    afts = canvas._collect_matching_afts(op1, op2)
    print(afts)


def test_raise_exception_if_wiring_two_inputs(session):
    canvas = Planner(session)
    assert len(canvas.plan.wires) == 0

    op1 = canvas.create_operation_by_name("Check Plate", category="Cloning")
    op2 = canvas.create_operation_by_name("Check Plate", category="Cloning")

    with pytest.raises(PlannerException):
        canvas.add_wire(op1.inputs[0], op2.inputs[0])


def test_raise_exception_if_wiring_two_outputs(session):
    canvas = Planner(session)
    assert len(canvas.plan.wires) == 0

    op1 = canvas.create_operation_by_name("Check Plate", category="Cloning")
    op2 = canvas.create_operation_by_name("Check Plate", category="Cloning")

    with pytest.raises(PlannerException):
        canvas.add_wire(op1.outputs[0], op2.outputs[0])


def test_canvas_add_op(session):

    canvas = Planner(session)
    canvas.create_operation_by_name("Yeast Transformation")
    canvas.create_operation_by_name("Yeast Antibiotic Plating")
    canvas.quick_wire_by_name("Yeast Transformation", "Yeast Antibiotic Plating")
    canvas.create()

    p = session.Plan.find(canvas.plan.id)
    pass


def test_canvas_quick_create_chain(session):
    canvas = Planner(session)

    canvas.chain(
        "Yeast Transformation", "Check Yeast Plate", "Yeast Overnight Suspension"
    )
    assert len(canvas.plan.operations) == 3
    assert len(canvas.plan.wires) == 2, "There should be two operations"


def test_chain_run_gel(session):
    canvas = Planner(session)
    canvas.chain("Make PCR Fragment", "Run Gel", category="Cloning")


def test_quick_chain_to_existing_operation(session):
    canvas = Planner(session)
    op = canvas.create_operation_by_name("Yeast Transformation")
    canvas.chain(op, "Check Yeast Plate")
    assert len(canvas.plan.wires) == 1


def test_quick_chain_to_existing_operation_too_many_times(session):
    canvas = Planner(session)
    op = canvas.create_operation_by_name("Yeast Transformation")
    op1 = canvas.chain(op, "Check Yeast Plate")[-1]
    with pytest.raises(PlannerException):
        canvas.chain("Yeast Transformation", op1)
    assert len(canvas.plan.wires) == 1


def test_canvas_chaining(session):
    canvas = Planner(session)
    canvas.browser.log.set_verbose(True)
    ops = canvas.chain(
        "Assemble Plasmid",
        "Transform Cells",
        "Plate Transformed Cells",
        "Check Plate",
        category="Cloning",
    )
    assert len(canvas.plan.wires) == 3
    new_ops = []
    for i in range(3):
        new_ops += canvas.chain(
            ops[-1], ("E Coli Lysate", "Cloning"), "E Coli Colony PCR"
        )[1:]
    assert len(canvas.plan.wires) == 2 * 3 + 3


def test_layout_edges_and_nodes(session):
    canvas = Planner(session)
    canvas.chain(
        "Yeast Transformation", "Check Yeast Plate", "Yeast Overnight Suspension"
    )
    G = canvas.layout.nxgraph
    edges = list(G.edges)
    assert len(edges) == 2, "There should only be 2 edges/wires in the graph/plan"
    assert (
        len(G.nodes) == 3
    ), "There should only be 3 nodes/Operations in the graph/plan"
    assert edges[0][1] == edges[1][0], "Check Yeast Plate should be in both wires"


def test_load_canvas(session):

    canvas = Planner(session.Plan.one())
    assert canvas is not None
    assert canvas.plan is not None
    assert canvas.plan.operations is not None


def test_proper_setting_of_object_types(session):

    canvas = Planner(session)
    yeast = session.Sample.where(
        {"sample_type_id": session.SampleType.find_by_name("Yeast Strain").id},
        opts={"limit": 10},
    )[-1]

    streak = canvas.create_operation_by_name("Streak Plate", category="Yeast")
    glycerol = canvas.create_operation_by_name("Yeast Glycerol Stock", category="Yeast")
    canvas.set_field_value(glycerol.inputs[0], sample=yeast)
    canvas.set_field_value(streak.inputs[0], sample=yeast)
    mating = canvas.create_operation_by_name("Yeast Mating")
    canvas.add_wire(streak.outputs[0], mating.inputs[0])
    canvas.add_wire(glycerol.outputs[0], mating.inputs[1])
    assert (
        mating.inputs[0].allowable_field_type.object_type.name == "Divided Yeast Plate"
    )
    assert (
        mating.inputs[1].allowable_field_type.object_type.name == "Yeast Glycerol Stock"
    )


def test_annotate(session):

    canvas = Planner(session)

    a = canvas.annotate("This is my annotation", 10, 20, 110, 100)

    assert a["x"] == 10
    assert a["y"] == 20
    anchor = a["anchor"]
    assert anchor["x"] == 110
    assert anchor["y"] == 100


def test_annotate_layout(session):

    canvas = Planner(session)

    ops = canvas.chain("Make PCR Fragment", "Run Gel", category="Cloning")
    canvas.layout.topo_sort()
    canvas.layout.move(100, 200)

    a = canvas.annotate_above_layout("This is an annotation", 100, 50)

    anchor = a["anchor"]
    xmidpoint = a["x"] + anchor["x"] / 2
    ybottom = a["y"] + anchor["y"]

    assert xmidpoint == 100 + canvas.layout.BOX_WIDTH / 2
    assert ybottom == 200 - canvas.layout.BOX_DELTA_Y / 2

    canvas.plan.name = "annotation test"
    canvas.create()
    print(canvas.url)


def test_routing_graph(session):

    canvas = Planner(session)
    ops = canvas.chain(
        "Rehydrate Primer",
        "Make PCR Fragment",
        "Run Gel",
        "Extract Gel Slice",
        "Purify Gel Slice",
        "Assemble Plasmid",
        category="Cloning",
    )

    routing_graph = canvas._routing_graph()
    print(get_subgraphs(routing_graph))


def test_quick_wire_to_input_array(session):
    canvas = Planner(session)
    ops = canvas.chain("Purify Gel Slice", "Assemble Plasmid", category="Cloning")
    canvas.chain("Purify Gel Slice", ops[-1], category="Cloning")

    assert len(canvas.plan.operations) == 3
    assert len(canvas.plan.wires) == 2


def test_quick_wire_to_input_array_and_then_set_sample(session):
    canvas = Planner(session)

    frags = session.Sample.where(
        {"sample_type_id": session.SampleType.find_by_name("Fragment").id},
        opts={"limit": 10},
    )

    purify1 = canvas.create_operation_by_name("Purify Gel Slice", category="Cloning")
    purify2 = canvas.create_operation_by_name("Purify Gel Slice", category="Cloning")

    assemble = canvas.create_operation_by_name("Assemble Plasmid", category="Cloning")

    canvas.quick_wire(purify1, assemble)
    canvas.quick_wire(purify2, assemble)

    canvas.set_field_value_and_propogate(purify1.inputs[0], sample=frags[0])

    input_array = assemble.input_array("Fragment")

    print("purify1: " + str(purify1.rid))
    print("purify2: " + str(purify2.rid))

    for i in input_array:
        print(
            i.operation.operation_type.name
            + " "
            + i.name
            + " "
            + str(i.sample)
            + " "
            + str(canvas.get_incoming_wires(i)[0].source.operation.rid)
        )

    print("ljljklj")
    print(purify2.outputs[0].sample)

    assert (
        assemble.input_array("Fragment")[0].sample == frags[0]
    ), "Setting a wire should propogate to a field value"
    assert assemble.input_array("Fragment")[1].sample is None, (
        "Setting a wire should not propogate sample to other field"
        "values in the input array."
    )


def test_quick_wire_to_input_array_with_set_sample(session):
    canvas = Planner(session)

    frags = session.Sample.where(
        {"sample_type_id": session.SampleType.find_by_name("Fragment").id},
        opts={"limit": 10},
    )

    purify1 = canvas.create_operation_by_name("Purify Gel Slice", category="Cloning")
    purify2 = canvas.create_operation_by_name("Purify Gel Slice", category="Cloning")

    canvas.set_field_value(purify1.inputs[0], sample=frags[0])
    canvas.set_field_value(purify2.inputs[0], sample=frags[1])

    assemble = canvas.create_operation_by_name("Assemble Plasmid", category="Cloning")

    canvas.quick_wire(purify1, assemble)
    canvas.quick_wire(purify2, assemble)

    canvas.chain("Purify Gel Slice", assemble, category="Cloning")

    input_array = assemble.input_array("Fragment")

    assert len(input_array) == 3, "There should be 3 field values"
    assert input_array[0].sample == frags[0]
    assert input_array[1].sample == frags[1]
    assert input_array[2].sample is None


# TODO: this test is not finished..
def test_set_output_and_propogate(session):
    session.set_verbose(True)
    canvas = Planner(session)
    ops = canvas.chain(
        "Rehydrate Primer",
        "Make PCR Fragment",
        "Run Gel",
        "Extract Gel Slice",
        "Purify Gel Slice",
        "Assemble Plasmid",
        category="Cloning",
    )

    example_fragment = session.Sample.find_by_name("SV40-dCas9-split")
    canvas.set_output_sample(
        ops[1].outputs[0],
        sample=example_fragment,
        setter=canvas.set_field_value_and_propogate,
    )

    canvas.validate()


def test_set_input_array(session):

    canvas = Planner(session)

    op = canvas.create_operation_by_name("Assemble Plasmid", category="Cloning")

    frags = session.Sample.where(
        {"sample_type_id": session.SampleType.find_by_name("Fragment").id},
        opts={"limit": 10},
    )

    canvas.set_input_field_value_array(op, "Fragment", sample=frags[0])
    canvas.set_input_field_value_array(op, "Fragment", sample=frags[1])

    input_array = op.input_array("Fragment")

    assert (
        len(op.input_array("Fragment")) == 2
    ), "There should be exactly 2 field values in the input array"
    assert (
        input_array[0] != input_array[1]
    ), "Input array field values should be different"

    assert len(op.input_array("Fragment")) == 2
    assert (
        op.input_array("Fragment")[0].sample == frags[0]
    ), "Input array 0 should have fragment 0"
    assert (
        op.input_array("Fragment")[1].sample == frags[1]
    ), "Input array 1 should have fragment 1"


def test_plan_validate_with_no_errors(session):
    """An easy to pass test.

    A plan that is complete should always pass the validation method.
    """
    session.set_verbose(True)
    plan = session.Plan.one(query='status != "planning"')
    assert plan
    canvas = Planner(plan)
    canvas.validate()
