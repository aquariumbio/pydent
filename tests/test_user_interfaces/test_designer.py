from pydent import designer

def test_add_operation_by_name(session):
    plan = session.Plan.find(121080)
    canvas = designer.Canvas(session, plan_id=121080)
    canvas.create_operation_by_name("Yeast Transformation")

def test_find_layout_inconsistencies(session):
    pass

def test_add_operation_by_id(session):
    pass

def test_remove_operation_by_id(session):
    pass

def test_find_operations_of_type(session):
    pass


class TestCanvasLayout:

    class FakeOp():
        rid = 0
        def __init__(self, x, y):
            self.x = x
            self.y = y
            self.id = self.__class__.rid
            self.__class__.rid += 1

    def test_layout(self, session):
        canvas = designer.Canvas(session)
        ops = canvas.quick_create_chain("Assemble Plasmid", "Transform Cells", "Plate Transformed Cells", "Check Plate",
                                        category="Cloning")
        assert canvas.layout is not None


    def test_bounds_of_ops(self):
        op1 = self.FakeOp(300, 50)
        op2 = self.FakeOp(100, 400)
        op3 = self.FakeOp(0, 700)
        ops = [op1, op2, op3]

        layout = designer.CanvasLayout()
        for op in ops:
            layout._add_operation(op)

        ul, lr = layout.bounds()

        assert ul == (0, 50)
        assert lr == (300, 700)

    def test_midpoint_of_ops(self):
        op1 = self.FakeOp(-100, 50)
        op2 = self.FakeOp(100, 400)
        op3 = self.FakeOp(300, 700)
        ops = [op1, op2, op3]

        layout = designer.CanvasLayout()
        for op in ops:
            layout._add_operation(op)

        x, y = layout.midpoint()

        assert x == 100, "Should 100"
        assert y == (700 - 50) / 2.0 + 50

    def test_translate_ops(self):
        op1 = self.FakeOp(0, 50)
        op2 = self.FakeOp(100, 400)
        op3 = self.FakeOp(300, 700)
        ops = [op1, op2, op3]

        layout = designer.CanvasLayout()
        for op in ops:
            layout._add_operation(op)

        layout.translate(-10, 30)
        assert op1.x == -10
        assert op2.y == 430

    def test_adjust_upper_left(self):
        op1 = self.FakeOp(0, 50)
        op2 = self.FakeOp(100, 400)
        op3 = self.FakeOp(300, 700)
        ops = [op1, op2, op3]

        layout = designer.CanvasLayout()
        for op in ops:
            layout._add_operation(op)

        layout.align_upper_left_to(100, 100)

        assert op1.x == 100
        assert op2.x == 200
        assert op3.x == 400

        assert op1.y == 100
        assert op2.y == 450
        assert op3.y == 750

    def test_align_x_with_predecessors(self, session):
        canvas = designer.Canvas(session)

        ops = canvas.quick_create_chain("Assemble Plasmid", "Transform Cells", "Plate Transformed Cells", "Check Plate", category="Cloning")

        for i in range(3):
            canvas.quick_create_chain(ops[-1], "E Coli Lysate", category="Cloning")

        new_ops = canvas.find_operations_by_name("E Coli Lysate")
        new_ops[0].x = 0
        new_ops[1].x = 100
        new_ops[2].x = 150

        ops_layout = canvas.layout.ops_to_subgraph(ops)
        new_op_layout = canvas.layout.ops_to_subgraph(new_ops)


        assert new_op_layout.midpoint()[0] != ops[-1].x
        new_op_layout.align_x_with_other(ops_layout)
        assert new_op_layout.midpoint()[0] == ops[-1].x

    def test_topo_sort(self, session):
        canvas = designer.Canvas(session)

        ops = canvas.quick_create_chain("Assemble Plasmid", "Transform Cells", "Plate Transformed Cells", "Check Plate", category="Cloning")

        for i in range(3):
            canvas.quick_create_chain(ops[-1], ("E Coli Lysate", "Cloning"), "E Coli Colony PCR")

        lysate = canvas.find_operations_by_name("E Coli Lysate")
        pcr = canvas.find_operations_by_name("E Coli Colony PCR")
        canvas.layout.topo_sort()
        assert canvas.layout.ops_to_subgraph(lysate).midpoint()[0] == ops[-1].x
        assert canvas.layout.ops_to_subgraph(lysate).midpoint()[0] == canvas.layout.ops_to_subgraph(pcr).midpoint()[0]

    def test_subgraph(self, session):
        canvas = designer.Canvas(session)
        ops = canvas.quick_create_chain("Assemble Plasmid", "Transform Cells", "Plate Transformed Cells", "Check Plate",
                                        category="Cloning")

        graph = canvas.layout.ops_to_subgraph(ops[-2:])
        assert len(graph) == 2
        canvas.layout.topo_sort()