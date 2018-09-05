from pydent import designer

def test_canvas_create(session):
    canvas = designer.Canvas(session)
    canvas.create()
    print(canvas.plan.id)


def test_canvas_add_op(session):

    canvas = designer.Canvas(session)
    canvas.create_operation_by_name("Yeast Transformation")
    canvas.create_operation_by_name("Yeast Antibiotic Plating")
    canvas.quick_wire("Yeast Transformation", "Yeast Antibiotic Plating")
    canvas.create()

    p = session.Plan.find(canvas.plan.id)
    pass

def test_canvas_chain(session):

    canvas = designer.Canvas(session)

    canvas.quick_create_chain("Yeast Transformation", "Check Yeast Plate", "Yeast Overnight Suspension")

    # print(canvas.plan.wires)
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


def test_layout(session):

    pass


def test_add_op(session):
    canvas = designer.Canvas(session, plan_id=23055)
    canvas.plan.validate(True)

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

