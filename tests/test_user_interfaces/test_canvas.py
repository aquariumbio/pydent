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
    from collections import OrderedDict

    canvas = designer.Canvas(session, plan_id=122133)
    G = canvas.networkx()
    sorted = list(nx.topological_sort(G))[::-1]
    # y = 100
    res = nx.single_source_shortest_path_length(G, sorted[-1])
    by_depth = OrderedDict()
    for k, v in res.items():
        by_depth.setdefault(v, [])
        by_depth[v].append(k)
    y = 100
    for depth, op_ids in reversed(list(by_depth.items())):
        x = 100
        for op_id in op_ids:
            op = G.node[op_id]['operation']
            op.x = x
            op.y = y
            x += 170
        y += 70
    canvas.save()
    print(canvas.url)

    # for n in list(nx.topological_sort(G))[::-1]:
    #     op = G.nodes[n]['operation']
    #     op.y = y
    #     y += 75
    # canvas.save()

    # canvas.draw()/
    # print(canvas.url)

