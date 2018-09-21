import pytest
from pydent.planner import Planner, PlannerException


def test_canvas_create(session):
    canvas = Planner(session)
    canvas.create()
    print(canvas.plan.id)


def test_raises_exception_wiring_with_no_afts(session):
    canvas = Planner(session)
    op1 = canvas.create_operation_by_name(
        "Make PCR Fragment", category="Cloning")
    op2 = canvas.create_operation_by_name("Check Plate", category="Cloning")

    with pytest.raises(PlannerException):
        canvas._set_wire(op1.outputs[0], op2.inputs[0])


def test_add_wire(session):
    canvas = Planner(session)
    assert len(canvas.plan.wires) == 0
    op1 = canvas.create_operation_by_name(
        "Make PCR Fragment", category="Cloning")
    op2 = canvas.create_operation_by_name(
        "Rehydrate Primer", category="Cloning")

    canvas.add_wire(op2.outputs[0], op1.input("Forward Primer"))
    assert len(canvas.plan.wires) == 1
    wire = canvas.plan.wires[0]
    assert wire.source.allowable_field_type.sample_type_id == wire.destination.allowable_field_type.sample_type_id
    assert wire.source.allowable_field_type.object_type_id == wire.destination.allowable_field_type.object_type_id


def test_add_wire_sets_sample_from_destination(session):
    canvas = Planner(session)
    assert len(canvas.plan.wires) == 0
    p = canvas.session.SampleType.find_by_name("Primer").samples[0]
    destination = canvas.create_operation_by_name(
        "Make PCR Fragment", category="Cloning")
    source = canvas.create_operation_by_name(
        "Rehydrate Primer", category="Cloning")
    canvas.set_field_value(destination.input("Forward Primer"), sample=p)
    canvas.add_wire(source.outputs[0], destination.input("Forward Primer"))
    assert source.outputs[0].sample == p


def test_add_wire_sets_sample_from_source(session):
    canvas = Planner(session)
    assert len(canvas.plan.wires) == 0
    p = canvas.session.SampleType.find_by_name("Primer").samples[0]
    destination = canvas.create_operation_by_name(
        "Make PCR Fragment", category="Cloning")
    source = canvas.create_operation_by_name(
        "Rehydrate Primer", category="Cloning")
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
    canvas.quick_wire_by_name("Yeast Transformation",
                              "Yeast Antibiotic Plating")
    canvas.create()

    p = session.Plan.find(canvas.plan.id)
    pass


def test_canvas_quick_create_chain(session):
    canvas = Planner(session)

    canvas.quick_create_chain("Yeast Transformation",
                              "Check Yeast Plate",
                              "Yeast Overnight Suspension")
    assert len(canvas.plan.operations) == 3
    assert len(canvas.plan.wires) == 2


def test_chain_run_gel(session):
    canvas = Planner(session)
    canvas.quick_create_chain(
        "Make PCR Fragment", "Run Gel", category="Cloning")


def test_quick_chain_to_existing_operation(session):
    canvas = Planner(session)
    op = canvas.create_operation_by_name("Yeast Transformation")
    canvas.quick_create_chain(op, "Check Yeast Plate")
    assert len(canvas.plan.wires) == 1


def test_canvas_chaining(session):
    canvas = Planner(session)
    ops = canvas.quick_create_chain("Assemble Plasmid", "Transform Cells",
                                    "Plate Transformed Cells", "Check Plate",
                                    category="Cloning")
    assert len(canvas.plan.wires) == 3
    new_ops = []
    for i in range(3):
        new_ops += canvas.quick_create_chain(
            ops[-1], ("E Coli Lysate", "Cloning"), "E Coli Colony PCR")[1:]
    assert len(canvas.plan.wires) == 2 * 3 + 3


def test_layout_edges_and_nodes(session):
    canvas = Planner(session)
    canvas.quick_create_chain("Yeast Transformation",
                              "Check Yeast Plate", "Yeast Overnight Suspension")
    G = canvas.layout.G
    edges = list(G.edges)
    assert len(edges) == 2, "There should only be 2 edges/wires in the graph/plan"
    assert len(
        G.nodes) == 3, "There should only be 3 nodes/Operations in the graph/plan"
    assert edges[0][1] == edges[1][0], "Check Yeast Plate should be in both wires"


def test_load_canvas(session):

    canvas = Planner(session, plan_id=122133)
    assert canvas is not None
    assert canvas.plan is not None
    assert canvas.plan.operations is not None


def test_proper_setting_of_object_types(session):

    canvas = Planner(session)
    yeast = session.Sample.where({"sample_type_id": session.SampleType.find_by_name("Yeast Strain").id}, opts={"limit": 10})[-1]

    streak = canvas.create_operation_by_name("Streak Plate", category="Yeast")
    glycerol = canvas.create_operation_by_name("Yeast Glycerol Stock", category="Yeast")
    canvas.set_field_value(glycerol.inputs[0], sample=yeast)
    canvas.set_field_value(streak.inputs[0], sample=yeast)
    mating = canvas.create_operation_by_name("Yeast Mating")
    canvas.add_wire(streak.outputs[0], mating.inputs[0])
    canvas.add_wire(glycerol.outputs[0], mating.inputs[1])
    assert mating.inputs[0].allowable_field_type.object_type.name == "Divided Yeast Plate"
    assert mating.inputs[1].allowable_field_type.object_type.name == "Yeast Glycerol Stock"
