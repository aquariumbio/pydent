import pytest
from pydent import designer


def test_canvas_create(session):
    canvas = designer.Canvas(session)
    canvas.create()
    print(canvas.plan.id)


def test_raises_exception_wiring_with_no_afts(session):
    canvas = designer.Canvas(session)
    op1 = canvas.create_operation_by_name("Make PCR Fragment", category="Cloning")
    op2 = canvas.create_operation_by_name("Check Plate", category="Cloning")

    with pytest.raises(designer.CanvasException):
        canvas._set_wire(op1.outputs[0], op2.inputs[0])


def test_add_wire(session):
    canvas = designer.Canvas(session)
    assert len(canvas.plan.wires) == 0
    op1 = canvas.create_operation_by_name("Make PCR Fragment", category="Cloning")
    op2 = canvas.create_operation_by_name("Rehydrate Primer", category="Cloning")

    canvas.add_wire(op2.outputs[0], op1.input("Forward Primer"))
    assert len(canvas.plan.wires) == 1
    wire = canvas.plan.wires[0]
    assert wire.source.allowable_field_type.sample_type_id == wire.destination.allowable_field_type.sample_type_id
    assert wire.source.allowable_field_type.object_type_id == wire.destination.allowable_field_type.object_type_id


def test_add_wire_sets_sample_from_destination(session):
    canvas = designer.Canvas(session)
    assert len(canvas.plan.wires) == 0
    p = canvas.session.SampleType.find_by_name("Primer").samples[0]
    destination = canvas.create_operation_by_name("Make PCR Fragment", category="Cloning")
    source = canvas.create_operation_by_name("Rehydrate Primer", category="Cloning")
    canvas.set_field_value(destination.input("Forward Primer"), sample=p)
    canvas.add_wire(source.outputs[0], destination.input("Forward Primer"))
    assert source.outputs[0].sample == p


def test_add_wire_sets_sample_from_source(session):
    canvas = designer.Canvas(session)
    assert len(canvas.plan.wires) == 0
    p = canvas.session.SampleType.find_by_name("Primer").samples[0]
    destination = canvas.create_operation_by_name("Make PCR Fragment", category="Cloning")
    source = canvas.create_operation_by_name("Rehydrate Primer", category="Cloning")
    canvas.set_field_value(source.outputs[0], sample=p)
    canvas.add_wire(source.outputs[0], destination.input("Forward Primer"))
    assert destination.input("Forward Primer").sample == p


def test_collect_matching_afts(session):
    canvas = designer.Canvas(session)

    op1 = canvas.create_operation_by_name("Check Plate", category="Cloning")
    op2 = canvas.create_operation_by_name("E Coli Lysate", category="Cloning")
    afts = canvas._collect_matching_afts(op1, op2)
    print(afts)

def test_raise_exception_if_wiring_two_inputs(session):
    canvas = designer.Canvas(session)
    assert len(canvas.plan.wires) == 0

    op1 = canvas.create_operation_by_name("Check Plate", category="Cloning")
    op2 = canvas.create_operation_by_name("Check Plate", category="Cloning")

    with pytest.raises(designer.CanvasException):
        canvas.add_wire(op1.inputs[0], op2.inputs[0])


def test_raise_exception_if_wiring_two_outputs(session):
    canvas = designer.Canvas(session)
    assert len(canvas.plan.wires) == 0

    op1 = canvas.create_operation_by_name("Check Plate", category="Cloning")
    op2 = canvas.create_operation_by_name("Check Plate", category="Cloning")

    with pytest.raises(designer.CanvasException):
        canvas.add_wire(op1.outputs[0], op2.outputs[0])


def test_canvas_add_op(session):

    canvas = designer.Canvas(session)
    canvas.create_operation_by_name("Yeast Transformation")
    canvas.create_operation_by_name("Yeast Antibiotic Plating")
    canvas.quick_wire_by_name("Yeast Transformation", "Yeast Antibiotic Plating")
    canvas.create()

    p = session.Plan.find(canvas.plan.id)
    pass


def test_canvas_quick_create_chain(session):

    canvas = designer.Canvas(session)

    canvas.quick_create_chain("Yeast Transformation", "Check Yeast Plate", "Yeast Overnight Suspension")
    assert len(canvas.plan.operations) == 3
    assert len(canvas.plan.wires) == 2


def test_chain_run_gel(session):
    canvas = designer.Canvas(session)
    canvas.quick_create_chain("Make PCR Fragment", "Run Gel", category="Cloning")


def test_quick_chain_to_existing_operation(session):
    canvas = designer.Canvas(session)
    op = canvas.create_operation_by_name("Yeast Transformation")
    canvas.quick_create_chain(op, "Check Yeast Plate")
    assert len(canvas.plan.wires) == 1

def test_canvas_chaining(session):
    canvas = designer.Canvas(session)
    ops = canvas.quick_create_chain("Assemble Plasmid", "Transform Cells", "Plate Transformed Cells", "Check Plate",
                                    category="Cloning")
    assert len(canvas.plan.wires) == 3
    new_ops = []
    for i in range(3):
        new_ops += canvas.quick_create_chain(ops[-1], ("E Coli Lysate", "Cloning"), "E Coli Colony PCR")[1:]
    assert len(canvas.plan.wires) == 2 * 3 + 3

def test_layout_edges_and_nodes(session):
    canvas = designer.Canvas(session)
    canvas.quick_create_chain("Yeast Transformation", "Check Yeast Plate", "Yeast Overnight Suspension")
    G = canvas.layout.G
    edges = list(G.edges)
    assert len(edges) == 2, "There should only be 2 edges/wires in the graph/plan"
    assert len(G.nodes) == 3, "There should only be 3 nodes/Operations in the graph/plan"
    assert edges[0][1] == edges[1][0], "Check Yeast Plate should be in both wires"


def test_load_canvas(session):

    canvas = designer.Canvas(session, plan_id=122133)
    assert canvas is not None
    assert canvas.plan is not None
    assert canvas.plan.operations is not None


def test_proper_setting_of_object_types(session):

    canvas = designer.Canvas(session)
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

def test_add_(session):
    from pydent import AqSession
    from pydent.utils import make_async

    production = AqSession("vrana", "Mountain5", "http://52.27.43.242/")

    guide_names = [
        "pMOD-LTR2-Bleo-pGRR-W8W20-RGR-W5",
        "pMOD-LTR2-Bleo-pGRR-W20W8-RGR-W5",
        "pMOD-LTR3-HygMX-pGRR-RGR-W36"
    ]

    find_by_name = lambda x: production.Sample.find_by_name(x)

    guides = [find_by_name(x) for x in guide_names]

    canvas = designer.Canvas(production, plan_id=25630)


    # preload
    @make_async(3)
    def foo(ops):
        for op in ops:
            op.operation_type

    plasmid_digests = canvas.find_operations_by_name("Plasmid Digest")

    for guide in guides:
        print(guide.name)
        op = canvas.create_operation_by_name("Make Overnight Suspension")
        glycerol_stocks = guide.available_items(object_type_name="Plasmid Glycerol Stock")
        canvas.set_field_value(op.inputs[0], sample=guide, item=glycerol_stocks[-1],
                               container=glycerol_stocks[-1].object_type)
        miniprep = canvas.quick_create_chain(op, "Make Miniprep")[-1]
        for plasmid_digest in plasmid_digests:
            if plasmid_digest.inputs[0].sample.id == guide.id:
                canvas.add_wire(miniprep.outputs[0], plasmid_digest.inputs[0])


    # # data = canvas.plan.to_save_json()
    #
    # op = canvas.get_operation(113772)
    #
    # op2 = canvas.create_operation_by_name("Fragment Analyzing")
    # # canvas.quick_wire_ops(op, op2)
    # # data = canvas.plan.to_save_json()
    # # import json
    # # with open('temp.json', 'w') as f:
    # #     json.dump(data, f)
    # canvas.save()


    # for op in canvas.plan.operations:



    # for n in list(nx.topological_sort(G))[::-1]:
    #     op = G.nodes[n]['operation']
    #     op.y = y
    #     y += 75
    # canvas.save()

    # canvas.draw()/
    # print(canvas.url)

