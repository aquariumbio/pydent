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
    G = canvas.networkx()
    print(G.edges)


def test_load_canvas(session):

    canvas = designer.Canvas(session, plan_id=122133)
    canvas.create_operation_by_name("Streak Plate")
    canvas.quick_wire("Yeast Overnight Suspension", "Streak Plate")
    canvas.save()

    print(canvas.url)
    # canvas.create()

    # print(canvas.url)

def test_topological_sort(session):
    import networkx as nx
    canvas = designer.Canvas(session, plan_id=122133)
    G = canvas.networkx()
    for n in nx.topological_sort(G):
        print(n)

