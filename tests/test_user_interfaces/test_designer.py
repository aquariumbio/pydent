from pydent import designer


def test_add_operation_by_name(session):
    plan = session.Plan.find(121080)
    op = designer.create_operation_by_name(plan, "Yeast Transformation")
    print(op.id)


def test_layout(session):
    plan = session.Plan.find(121081)
    layout = plan.layout
    pass


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

        def __init__(self, x, y):
            self.x = x
            self.y = y

    def test_bounds_of_ops(self):
        op1 = self.FakeOp(300, 50)
        op2 = self.FakeOp(100, 400)
        op3 = self.FakeOp(0, 700)
        ops = [op1, op2, op3]

        ul, lr = designer.Canvas.bounds_of_ops(ops)

        assert ul == (0, 50)
        assert lr == (300, 700)

    def test_midpoint_of_ops(self):
        op1 = self.FakeOp(-100, 50)
        op2 = self.FakeOp(100, 400)
        op3 = self.FakeOp(300, 700)
        x, y = designer.Canvas.midpoint_of_ops([op1, op2, op3])

        assert x == 100, "Should 100"
        assert y == (700 - 50) / 2.0 + 50

    def test_translate_ops(self):
        op1 = self.FakeOp(0, 50)
        op2 = self.FakeOp(100, 400)
        op3 = self.FakeOp(300, 700)
        ops = [op1, op2, op3]

        designer.Canvas.translate_ops(ops, -10, 30)
        assert op1.x == -10
        assert op2.y == 430

    def test_adjust_upper_left(self):
        op1 = self.FakeOp(0, 50)
        op2 = self.FakeOp(100, 400)
        op3 = self.FakeOp(300, 700)
        ops = [op1, op2, op3]

        designer.Canvas.adjust_upper_left(ops, 100, 100)

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


        assert canvas.midpoint_of_ops(new_ops)[0] != ops[-1].x
        for op in new_ops:
            print("{} {}".format(op.x, op.y))
        canvas.align_x_with_predecessors(new_ops)
        for op in new_ops:
            print("{} {}".format(op.x, op.y))
        assert canvas.midpoint_of_ops(new_ops)[0] == ops[-1].x

    def test_topo_sort(self, session):
        canvas = designer.Canvas(session)

        ops = canvas.quick_create_chain("Assemble Plasmid", "Transform Cells", "Plate Transformed Cells", "Check Plate", category="Cloning")
        new_ops = []

        for i in range(3):
            canvas.quick_create_chain(ops[-1], ("E Coli Lysate", "Cloning"), "E Coli Colony PCR")

        lysate = canvas.find_operations_by_name("E Coli Lysate")
        pcr = canvas.find_operations_by_name("E Coli Colony PCR")
        canvas.topo_sort()
        assert canvas.midpoint_of_ops(lysate)[0] == ops[-1].x
        assert canvas.midpoint_of_ops(lysate)[0] == canvas.midpoint_of_ops(pcr)[0]

# add wire

# remove wire

# validate plan

# update plan

# new plan

# move operation

# create a new layout

# create a new module

# create intra-plan wire

# propogate sample and items along wires