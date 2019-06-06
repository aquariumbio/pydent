from pydent.planner import Planner, PlannerLayout
from pydent import ModelBase

def test_add_operation_by_name(session):
    canvas = Planner(session, plan_id=121080)
    canvas.create_operation_by_name("Yeast Transformation")


class TestCanvasLayout:
    class FakeOp(ModelBase):
        rid = 0

        def __init__(self, x, y):
            self.x = x
            self.y = y
            self.id = self.__class__.rid
            self.__class__.rid += 1

    def test_layout(self, session):
        canvas = Planner(session)
        canvas.quick_create_chain("Assemble Plasmid", "Transform Cells",
                                  "Plate Transformed Cells", "Check Plate",
                                  category="Cloning")
        assert canvas.layout is not None

    def test_bounds_of_ops(self):
        op1 = self.FakeOp(300, 50)
        op2 = self.FakeOp(100, 400)
        op3 = self.FakeOp(0, 700)
        ops = [op1, op2, op3]

        layout = PlannerLayout()
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

        layout = PlannerLayout()
        for op in ops:
            layout._add_operation(op)

        x, y = layout.midpoint()

        assert x == 100, "Should 100"
        assert y == (700 - 50) / 2.0 + 50

    def test_height_and_width(self):
        op1 = self.FakeOp(-100, 50)
        op2 = self.FakeOp(100, 400)
        op3 = self.FakeOp(300, 700)
        ops = [op1, op2, op3]

        layout = PlannerLayout()
        for op in ops:
            layout._add_operation(op)

        assert layout.height == 650
        assert layout.width == 400

    def test_translate_ops(self):
        op1 = self.FakeOp(0, 50)
        op2 = self.FakeOp(100, 400)
        op3 = self.FakeOp(300, 700)
        ops = [op1, op2, op3]

        layout = PlannerLayout()
        for op in ops:
            layout._add_operation(op)

        layout.translate(-10, 30)
        assert op1.x == -10
        assert op2.y == 430

    def test_xy(self):
        op1 = self.FakeOp(0, 50)
        op2 = self.FakeOp(100, 400)
        op3 = self.FakeOp(300, 700)
        ops = [op1, op2, op3]

        layout = PlannerLayout()
        for op in ops:
            layout._add_operation(op)

        assert layout.x == 0
        assert layout.y == 50
        assert layout.xy == (0, 50)

    def test_x_setter(self):
        op1 = self.FakeOp(0, 50)
        op2 = self.FakeOp(100, 400)
        op3 = self.FakeOp(300, 700)
        ops = [op1, op2, op3]

        layout = PlannerLayout()
        for op in ops:
            layout._add_operation(op)

        layout.x = 75
        assert layout.x == 75
        assert op1.x == 75
        assert op2.x == 175
        assert op3.x == 375

    def test_y_setter(self):
        op1 = self.FakeOp(0, 50)
        op2 = self.FakeOp(100, 400)
        op3 = self.FakeOp(300, 700)
        ops = [op1, op2, op3]

        layout = PlannerLayout()
        for op in ops:
            layout._add_operation(op)

        layout.y = 0
        assert layout.y == 0
        assert op1.y == 0
        assert op2.y == 350
        assert op3.y == 650

    def test_move(self):
        op1 = self.FakeOp(0, 50)
        op2 = self.FakeOp(100, 400)
        op3 = self.FakeOp(300, 700)
        ops = [op1, op2, op3]

        layout = PlannerLayout()
        for op in ops:
            layout._add_operation(op)

        layout.move(100, 100)

        assert op1.x == 100
        assert op2.x == 200
        assert op3.x == 400

        assert op1.y == 100
        assert op2.y == 450
        assert op3.y == 750

    def test_collect_successors(self, session):
        canvas = Planner(session)
        ops = canvas.quick_create_chain("Assemble Plasmid", "Transform Cells",
                                        "Plate Transformed Cells",
                                        "Check Plate", category="Cloning")
        print(canvas.layout.ops_to_nodes(ops))
        s = canvas.layout.collect_successors(["r{}".format(ops[0].rid)])
        assert s == ["r{}".format(ops[1].rid)]

    def test_collect_predecessors(self, session):
        canvas = Planner(session)
        ops = canvas.quick_create_chain("Assemble Plasmid", "Transform Cells",
                                        "Plate Transformed Cells",
                                        "Check Plate", category="Cloning")
        s = canvas.layout.collect_predecessors(["r{}".format(ops[1].rid)])
        assert s == ["r{}".format(ops[0].rid)]

    def test_align_x_with_predecessors(self, session):
        canvas = Planner(session)

        ops = canvas.quick_create_chain("Assemble Plasmid", "Transform Cells",
                                        "Plate Transformed Cells",
                                        "Check Plate", category="Cloning")
        new_ops = canvas.find_operations_by_name("E Coli Lysate")
        print(len(new_ops))
        for _ in range(3):
            print('created')
            canvas.quick_create_chain(
                ops[-1], "E Coli Lysate", category="Cloning")
        new_ops = canvas.find_operations_by_name("E Coli Lysate")
        print(len(new_ops))
        new_ops[0].x = 0
        new_ops[1].x = 100
        new_ops[2].x = 150

        ops_layout = canvas.layout.ops_to_layout(ops)
        new_op_layout = canvas.layout.ops_to_layout(new_ops)

        midpoint = new_op_layout.midpoint()
        assert midpoint[0] == 75, "should be midpoint between 0 and 150"
        assert midpoint[0] != ops_layout.midpoint()[0]
        new_op_layout.align_x_midpoints_to(ops_layout)
        for op in new_op_layout.operations:
            print(op.rid)
            print(op.x)
        print()
        assert new_op_layout.midpoint()[0] == ops_layout.midpoint()[0]

    def test_successor_layout(self, session):
        canvas = Planner(session)

        ops = canvas.quick_create_chain("Assemble Plasmid", "Transform Cells",
                                        "Plate Transformed Cells",
                                        "Check Plate",
                                        category="Cloning")
        new_ops = []
        for _ in range(3):
            new_ops += canvas.quick_create_chain(
                ops[-1], ("E Coli Lysate", "Cloning"), "E Coli Colony PCR")[1:]
        assert len(new_ops) == 6
        successor_layout = canvas.layout.successor_layout(
            canvas.layout.ops_to_layout(ops))
        assert len(successor_layout) == 3

    def test_predecessor_layout(self, session):
        canvas = Planner(session)

        ops = canvas.quick_create_chain("Assemble Plasmid", "Transform Cells",
                                        "Plate Transformed Cells",
                                        "Check Plate",
                                        category="Cloning")
        new_ops = []
        for _ in range(3):
            new_ops += canvas.quick_create_chain(
                ops[-1], ("E Coli Lysate", "Cloning"), "E Coli Colony PCR")[1:]
        assert len(new_ops) == 6
        predecessor_layout = canvas.layout.predecessor_layout(
            canvas.layout.ops_to_layout(new_ops))
        assert len(predecessor_layout) == 1

    def test_align_midpoints(self, session):
        canvas = Planner(session)

        ops = canvas.quick_create_chain("Assemble Plasmid", "Transform Cells",
                                        "Plate Transformed Cells",
                                        "Check Plate",
                                        category="Cloning")
        new_ops = []
        for _ in range(3):
            new_ops += canvas.quick_create_chain(
                ops[-1], ("E Coli Lysate", "Cloning"), "E Coli Colony PCR")[1:]

        layout = canvas.layout.ops_to_layout(ops)
        successors = canvas.layout.successor_layout(layout)
        ops[-1].x = 400
        successors.align_x_midpoints_to(layout)

        assert successors.midpoint()[0] == layout.midpoint()[0]

    def test_topo_sort_chain(self, session):
        canvas = Planner(session)

        ops = canvas.quick_create_chain("Assemble Plasmid", "Transform Cells",
                                        "Plate Transformed Cells",
                                        "Check Plate",
                                        category="Cloning")
        ops[-1].x = 300
        ops[-2].x = 200
        ops[-3].x = 100

        assert not len(set([op.x for op in ops])) == 1
        canvas.layout.topo_sort()
        assert len(set([op.x for op in ops])) == 1

    def test_topo_sort(self, session):
        canvas = Planner(session)

        ops = canvas.quick_create_chain("Assemble Plasmid", "Transform Cells",
                                        "Plate Transformed Cells",
                                        "Check Plate",
                                        category="Cloning")
        ops[-1].x = 500
        for _ in range(3):
            canvas.quick_create_chain(
                ops[-1], ("E Coli Lysate", "Cloning"), "E Coli Colony PCR")

        lysate = canvas.find_operations_by_name("E Coli Lysate")
        pcr = canvas.find_operations_by_name("E Coli Colony PCR")
        canvas.layout.ops_to_layout(pcr).translate(100, 100)
        assert not canvas.layout.ops_to_layout(
            lysate).midpoint()[0] == ops[-1].x
        assert not canvas.layout.ops_to_layout(lysate).midpoint(
        )[0] == canvas.layout.ops_to_layout(pcr).midpoint()[0]
        canvas.layout.topo_sort()
        assert canvas.layout.ops_to_layout(lysate).midpoint()[0] == ops[-1].x
        assert canvas.layout.ops_to_layout(lysate).midpoint(
        )[0] == canvas.layout.ops_to_layout(pcr).midpoint()[0]

    def test_topo_sort_with_independent_subgraphs(self, session):
        canvas = Planner(session)

        ops1 = canvas.quick_create_chain(
            "Assemble Plasmid", "Transform Cells", "Plate Transformed Cells",
            category="Cloning")
        ops2 = canvas.quick_create_chain(
            "Assemble Plasmid", "Transform Cells", "Plate Transformed Cells",
            category="Cloning")
        ops3 = canvas.quick_create_chain(
            "Assemble Plasmid", "Transform Cells", "Plate Transformed Cells",
            category="Cloning")
        canvas.layout.topo_sort()
        print([op.x for op in ops1])
        print([op.x for op in ops2])
        print([op.x for op in ops3])
        assert ops3[0].x + canvas.layout.BOX_DELTA_X == ops2[0].x
        assert ops2[0].x + canvas.layout.BOX_DELTA_X == ops1[0].x

    def test_subgraph(self, session):
        canvas = Planner(session)
        ops = canvas.quick_create_chain("Assemble Plasmid", "Transform Cells",
                                        "Plate Transformed Cells",
                                        "Check Plate",
                                        category="Cloning")

        graph = canvas.layout.ops_to_layout(ops[-2:])
        assert len(graph) == 2
        canvas.layout.topo_sort()

    def test_leaves(self, session):
        canvas = Planner(session)
        ops = canvas.quick_create_chain("Assemble Plasmid", "Transform Cells",
                                        "Plate Transformed Cells",
                                        "Check Plate",
                                        category="Cloning")
        canvas.quick_create_chain(ops[0], "Transform Cells",
                                  "Plate Transformed Cells",
                                  "Check Plate",
                                  category="Cloning")
        assert len(canvas.layout.leaves()) == 2

    def test_roots(self, session):
        canvas = Planner(session)
        ops = canvas.quick_create_chain("Assemble Plasmid",
                                        "Transform Cells",
                                        "Plate Transformed Cells",
                                        "Check Plate",
                                        category="Cloning")
        canvas.quick_create_chain(ops[0], "Transform Cells",
                                  "Plate Transformed Cells",
                                  "Check Plate",
                                  category="Cloning")
        assert len(canvas.layout.roots()) == 1
