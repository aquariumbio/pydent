import pytest

from pydent.planner import Planner


@pytest.mark.record_mode("no")
@pytest.fixture(scope="function")
def planner_example(session):
    num_chains = 4
    with session.with_cache() as sess:
        p = Planner(sess)
        for _ in range(num_chains):
            p.chain(
                "Make PCR Fragment", "Run Gel", "Extract Gel Slice", "Purify Gel Slice"
            )
    p.plan.id = 1234
    return p


# def test_planner_autofill(session):
#
#     canvas = Planner(session)
#
#     chain = [
#         "Check Plate",
#         "Make Overnight Suspension",
#         "Make Miniprep",
#         "Yeast Transformation",
#         "Yeast Overnight Suspension",
#     ]
#
#     ops = canvas.chain(*chain)
#
#     assert canvas.validate()
#     canvas.autofill()
#     assert not canvas.validate()


def test_load_plans(session):
    with session.with_cache() as sess:
        ops = sess.Operation.last(10, query={"status": "done"})
        plans = sess.browser.get("Operation", "plans")

    for plan in plans:
        Planner(plan)


def test_add_successive_operations(session):
    p = Planner(session)
    p.create_operation_by_name("Make PCR Fragment")
    p.create_operation_by_name("Run Gel")
    assert len(p.plan.operations) == 2


def test_add_successive_operations_with_browser_session(session):
    with session.with_cache() as sess:
        p = Planner(sess)
        p.create_operation_by_name("Make PCR Fragment")
        p.create_operation_by_name("Run Gel")
    assert len(p.plan.operations) == 2


@pytest.mark.record_mode("no")
def test_copy_planner(planner_example):
    copied = planner_example.copy()
    assert planner_example.plan.id is not None
    assert copied.plan.id is None
    for op in copied.plan.operations:
        assert op.id is None
        assert op.operation_type_id
        assert op.field_values
        for fv in op.field_values:
            assert fv.parent_id is None
    for wire in copied.plan.wires:
        assert wire.source
        assert wire.destination
        assert wire.source.parent_id is None
        assert wire.destination.parent_id is None
    assert planner_example.layout


@pytest.mark.record_mode("no")
def test_split_planner(planner_example):
    plans = planner_example.split()
    assert len(plans) == 4


@pytest.mark.record_mode("no")
def test_combine_plans(planner_example):
    plans = planner_example.split()
    combined = Planner.combine(plans)

    assert len(combined.plan.operations) == len(
        planner_example.plan.operations
    ), "number of operations should remain the same"
    assert len(combined.plan.wires) == len(
        planner_example.plan.wires
    ), "number of wires should remain the same"


# TODO: more tests for setting items
@pytest.mark.parametrize("restrict_to_one", [True, False])
class TestSetItem:
    def test_restrict_to_one(self, session, restrict_to_one):
        with session.with_cache() as sess:
            sess.set_verbose(True)
            p = Planner(sess)
            for i in range(2):

                comp_cell_type = session.ObjectType.find_by_name("Yeast Competent Cell")
                comp_cells = session.Item.last(
                    100,
                    query='object_type_id = {} AND location != "deleted"'.format(
                        comp_cell_type.id
                    ),
                )
                grouped_by_samples = {}
                for c in comp_cells:
                    grouped_by_samples.setdefault(c.sample_id, list()).append(c)
                more_than_one = [
                    cells for cells in grouped_by_samples.values() if len(cells) > 1
                ][0]
                assert more_than_one
                parent_sample = more_than_one[0].sample

                op = p.create_operation_by_name("Yeast Transformation")
                p.set_field_value(op.input("Parent"), sample=parent_sample)
                if restrict_to_one:
                    p.set_to_available_item(
                        op.input("Parent"),
                        item_preference=p.ITEM_SELECTION_PREFERENCE.RESTRICT_TO_ONE,
                    )
                else:
                    p.set_to_available_item(op.input("Parent"))
            items = set()
            for op in p.plan.operations:
                for fv in op.field_values:
                    if fv.child_item_id:
                        items.add(fv.child_item_id)
            if restrict_to_one:
                assert len(items) == 2
            else:
                assert len(items) == 1


def test_prettify(session):
    with session.with_cache() as sess:
        canvas = Planner(sess)
        chain = [
            "Check Plate",
            "Make Overnight Suspension",
            "Make Miniprep",
            "Yeast Transformation",
            "Yeast Overnight Suspension",
        ]

        ops = canvas.chain(*chain)
        canvas.set_field_value_and_propogate(ops[0].inputs[0])
        canvas.set_to_available_item(ops[0].inputs[0])

        ops = canvas.chain(*chain)
        canvas.set_field_value_and_propogate(ops[0].inputs[0])
        canvas.set_to_available_item(ops[0].inputs[0])

        canvas.prettify()


def test_prettify(session):
    with session.with_cache() as sess:
        canvas = Planner(sess)

        for i in range(10):
            canvas.create_operation_by_name("Yeast Overnight Suspension")

        canvas.prettify()


# TODO: test ignore operations and other settings
class TestOptimizePlan:
    class Not:
        def __init__(self, v):
            self.v = v

    def sql(self, data):
        rows = []
        for k, v in data.items():
            if not isinstance(v, self.Not):
                rows.append('{} = "{}"'.format(k, v))
            else:
                rows.append('{} != "{}"'.format(k, v.v))
        return " AND ".join(rows)

    def test_optimize(self, session):

        with session.with_cache() as sess:
            canvas = Planner(sess)

            q = self.sql(
                {
                    "object_type_id": sess.ObjectType.find_by_name("Plasmid Stock").id,
                    "location": self.Not("deleted"),
                }
            )
            item = sess.Item.one(query=q)
            assert item

            ops = canvas.chain(
                "Make Miniprep", "Yeast Transformation", "Yeast Overnight Suspension"
            )

            canvas.set_field_value_and_propogate(ops[0].inputs[0], sample=item.sample)
            canvas.set_to_available_item(ops[0].inputs[0])

            ops = canvas.chain(
                "Make Miniprep", "Yeast Transformation", "Yeast Overnight Suspension"
            )

            canvas.set_field_value_and_propogate(ops[0].inputs[0], sample=item.sample)
            canvas.set_to_available_item(ops[0].inputs[0])

            assert len(canvas.plan.operations) == 6

            canvas.optimize()

            assert len(canvas.plan.operations) == 5

    def test_optimize_case1(self, session):
        """Here, we are trying to optimize two chains of 5 operations.

        Since Yeast Transformation is missing an input sample and Yeast
        Overnight Suspension is missing a output sample, these will NOT
        be merged, and so we expect 7 operations after the merge
        procedure.
        """
        with session.with_cache() as sess:
            canvas = Planner(sess)

            q = self.sql(
                {
                    "object_type_id": sess.ObjectType.find_by_name(
                        "E coli Plate of Plasmid"
                    ).id,
                    "location": self.Not("deleted"),
                }
            )
            item = sess.Item.one(query=q)
            assert item

            chain = [
                "Check Plate",
                "Make Overnight Suspension",
                "Make Miniprep",
                "Yeast Transformation",
                "Yeast Overnight Suspension",
            ]

            for i in range(2):
                ops = canvas.chain(*chain)
                canvas.set_field_value_and_propogate(
                    ops[0].inputs[0], sample=item.sample
                )
                canvas.set_to_available_item(ops[0].inputs[0])

            assert len(canvas.plan.operations) == 10

            canvas.optimize()

            # we expect to merge everything except 'Yeast Transformation' and
            # 'Yeast Overnight' since these have absent sample definition for either
            # their input or outputs and FieldValues with no samples are never mergable.
            expected_op_types = [
                "Check Plate",
                "Make Miniprep",
                "Make Overnight Suspension",
                "Yeast Overnight Suspension",
                "Yeast Overnight Suspension",
                "Yeast Transformation",
                "Yeast Transformation",
            ]
            op_types = sorted([op.operation_type.name for op in canvas.operations])
            assert len(canvas.plan.operations) == 7
            assert expected_op_types == op_types

    def test_optimize_case2(self, session):
        """Here, we are trying to optimize two chains of 5 operations.

        We expect to merge 10 operation to 5 operations.
        """
        with session.with_cache() as sess:
            canvas = Planner(sess)

            q = self.sql(
                {
                    "object_type_id": sess.ObjectType.find_by_name(
                        "E coli Plate of Plasmid"
                    ).id,
                    "location": self.Not("deleted"),
                }
            )
            item = sess.Item.one(query=q)
            assert item

            chain = [
                "Check Plate",
                "Make Overnight Suspension",
                "Make Miniprep",
                "Yeast Transformation",
                "Yeast Overnight Suspension",
            ]

            yeasts = session.Sample.last(
                2,
                query={
                    "sample_type_id": session.SampleType.find_by_name("Yeast Strain").id
                },
            )

            for i in range(2):
                ops = canvas.chain(*chain)
                canvas.set_field_value_and_propogate(
                    ops[0].inputs[0], sample=item.sample
                )
                canvas.set_to_available_item(ops[0].inputs[0])
                canvas.set_field_value_and_propogate(
                    ops[-1].outputs[0], sample=yeasts[0]
                )
                canvas.set_field_value(ops[-2].inputs[1], sample=yeasts[1])
            assert len(canvas.plan.operations) == 10

            canvas.optimize()

            # we expect to merge everything except 'Yeast Transformation' and
            # 'Yeast Overnight' since these have absent sample definition for either
            # their input or outputs and FieldValues with no samples are never mergable.
            expected_op_types = [
                "Check Plate",
                "Make Miniprep",
                "Make Overnight Suspension",
                "Yeast Overnight Suspension",
                "Yeast Transformation",
            ]
            op_types = sorted([op.operation_type.name for op in canvas.operations])
            assert len(canvas.plan.operations) == 5
            assert expected_op_types == op_types

    def test_optimize3(self, session):
        """Here we setup two operations chains of 5.

        6 of these operations will be mergable (10 to 7). We also add
        additional operations to one of the Miniprep operations. We
        should end up with 9 operations after the optimization.
        Additionally, the merged Miniprep should have a single output
        with 3 wires.
        """
        with session.with_cache() as sess:
            canvas = Planner(sess)

            q = self.sql(
                {
                    "object_type_id": sess.ObjectType.find_by_name(
                        "E coli Plate of Plasmid"
                    ).id,
                    "location": self.Not("deleted"),
                }
            )
            item = sess.Item.one(query=q)
            assert item

            chain = [
                "Check Plate",
                "Make Overnight Suspension",
                "Make Miniprep",
                "Yeast Transformation",
                "Yeast Overnight Suspension",
            ]

            ops = canvas.chain(*chain)
            canvas.set_field_value_and_propogate(ops[0].inputs[0], sample=item.sample)
            canvas.set_to_available_item(ops[0].inputs[0])
            ops[-1].tagged = "YES"

            ops = canvas.chain(*chain)
            canvas.set_field_value_and_propogate(ops[0].inputs[0], sample=item.sample)
            canvas.set_to_available_item(ops[0].inputs[0])

            canvas.chain(ops[2], "Yeast Transformation")
            canvas.chain(ops[2], "Make PCR Fragment")

            assert len(canvas.plan.operations) == 12
            assert len(canvas.get_outgoing_wires(ops[2].outputs[0])) == 3

            canvas.optimize()

            assert len(canvas.plan.operations) == 9
            assert len(canvas.get_outgoing_wires(ops[2].outputs[0])) == 4
            for yt in canvas.get_op_by_name("Yeast Transformation"):
                print(yt.inputs[0].name)
                assert len(canvas.get_incoming_wires(yt.inputs[0]))

    def test_optimize_case3_array_inputs(self, session):
        """Here we test whether operation types with field_value array inputs
        are mergable despite being in a different order."""
        with session.with_cache() as sess:
            canvas = Planner(sess)

            q = self.sql(
                {
                    "object_type_id": sess.ObjectType.find_by_name("Fragment Stock").id,
                    "location": self.Not("deleted"),
                }
            )
            items = sess.Item.last(4, query=q)
            assert items

            assemble_op1 = canvas.create_operation_by_name("Assemble Plasmid")
            assemble_op2 = canvas.create_operation_by_name("Assemble Plasmid")
            assemble_op3 = canvas.create_operation_by_name("Assemble Plasmid")
            assemble_op4 = canvas.create_operation_by_name("Assemble Plasmid")

            assemble_op1.add_to_input_array("Fragment", item=items[0])
            assemble_op1.add_to_input_array("Fragment", item=items[1])

            assemble_op2.add_to_input_array("Fragment", item=items[0])
            assemble_op2.add_to_input_array("Fragment", item=items[1])

            assemble_op3.add_to_input_array("Fragment", item=items[1])
            assemble_op3.add_to_input_array("Fragment", item=items[0])

            assemble_op4.add_to_input_array("Fragment", item=items[1])
            assemble_op4.add_to_input_array("Fragment", item=items[2])

            sample = sess.Sample.one(
                query={"sample_type_id": sess.SampleType.find_by_name("Plasmid").id}
            )
            canvas.set_field_value(assemble_op1.outputs[0], sample=sample)
            canvas.set_field_value(assemble_op2.outputs[0], sample=sample)
            canvas.set_field_value(assemble_op3.outputs[0], sample=sample)
            canvas.set_field_value(assemble_op4.outputs[0], sample=sample)

            assert len(canvas.plan.operations) == 4

            canvas.optimize()

            assert len(canvas.plan.operations) == 2

    def test_optimization_case4(self, session):
        """This tests that, even if an operation has the same field_value
        settings, if one of its input wires is wired from a different
        operation_type, it will not be merged."""
        with session.with_cache() as sess:
            canvas = Planner(sess)

            q = self.sql(
                {
                    "object_type_id": sess.ObjectType.find_by_name(
                        "Plasmid Glycerol Stock"
                    ).id,
                    "location": self.Not("deleted"),
                }
            )
            item = sess.Item.one(query=q)

            chain1 = [
                "Check Plate",
                "Make Overnight Suspension",
                "Make Miniprep",
                "Plasmid Digest",
            ]

            chain2 = ["Make Overnight Suspension", "Make Miniprep", "Plasmid Digest"]

            ops = canvas.chain(*chain1)
            canvas.set_field_value_and_propogate(ops[-1].outputs[0], sample=item.sample)

            ops = canvas.chain(*chain2)
            canvas.set_field_value_and_propogate(ops[0].inputs[0], item=item)

            assert len(canvas.operations) == 7

            canvas.optimize()

            assert len(canvas.operations) == 7

    def test_optimize_case4_array_inputs(self, session):
        with session.with_cache() as sess:

            canvas = Planner(sess)
            canvas.logger.set_level("DEBUG")
            q = self.sql(
                {
                    "object_type_id": sess.ObjectType.find_by_name("Fragment Stock").id,
                    "location": self.Not("deleted"),
                }
            )

            primers = sess.Sample.last(
                4, query={"sample_type_id": sess.SampleType.find_by_name("Primer").id}
            )

            fragments = sess.Sample.last(
                4, query={"sample_type_id": sess.SampleType.find_by_name("Fragment").id}
            )

            plasmids = sess.Sample.last(
                3, query={"sample_type_id": sess.SampleType.find_by_name("Plasmid").id}
            )

            subchain = [
                "Make PCR Fragment",
                "Run Gel",
                "Extract Gel Slice",
                "Purify Gel Slice",
            ]

            ops1 = canvas.chain(*(subchain + ["Assemble Plasmid"]))
            ops2 = canvas.chain(*(subchain + ops1[-1:]))

            ops3 = canvas.chain(*(subchain + ["Assemble Plasmid"]))
            ops4 = canvas.chain(*(subchain + ops3[-1:]))

            for ops in [ops1, ops2, ops3, ops4]:
                pour_gel = canvas.chain("Pour Gel", ops[1])[0]

            # pour_gels = [op for op in canvas.operations if
            #              op.operation_type.name == 'Pour Gel']
            # print([op.outputs[0].sample for op in pour_gels])

            # chain1 using primer1
            canvas.set_field_value_and_propogate(
                ops1[0].outputs[0], sample=fragments[0]
            )
            # chain2 using primer2
            canvas.set_field_value_and_propogate(
                ops2[0].outputs[0], sample=fragments[1]
            )

            # chain3 using primer2
            canvas.set_field_value_and_propogate(
                ops3[0].outputs[0], sample=fragments[1]
            )
            # chain4 using primer1
            canvas.set_field_value_and_propogate(
                ops4[0].outputs[0], sample=fragments[0]
            )

            def pcr(op, p1, p2, t):
                canvas.set_field_value(op.input("Forward Primer"), sample=p1)
                canvas.set_field_value(op.input("Reverse Primer"), sample=p2)
                canvas.set_field_value(op.input("Template"), sample=t)

            pcr(ops1[0], primers[0], primers[1], plasmids[0])
            pcr(ops2[0], primers[2], primers[3], plasmids[1])
            pcr(ops4[0], primers[0], primers[1], plasmids[0])
            pcr(ops3[0], primers[2], primers[3], plasmids[1])

            canvas.set_field_value(ops1[-1].outputs[0], sample=plasmids[2])
            canvas.set_field_value(ops3[-1].outputs[0], sample=plasmids[2])

            op_types = sorted([op.operation_type.name for op in canvas.operations])
            print(op_types)

            canvas.optimize()

            canvas.prettify()
            canvas.save()
            canvas.open()

            op_types = sorted([op.operation_type.name for op in canvas.operations])
            print(op_types)
            assert len(canvas.get_op_by_name("Assemble Plasmid")) == 1
            for op in canvas.get_op_by_name("Assemble Plasmid"):
                assert len({fv.child_sample_id for fv in op.inputs}) == 2
                assert len(op.inputs) == 2

                for input_fv in op.inputs:
                    assert len(canvas.get_incoming_wires(input_fv)) == 1

            assert len(canvas.get_op_by_name("Pour Gel")) == 2

    def test_optimize_case5_array_inputs(self, session):
        with session.with_cache() as sess:

            canvas = Planner(sess)
            canvas.logger.set_level("DEBUG")
            q = self.sql(
                {
                    "object_type_id": sess.ObjectType.find_by_name("Fragment Stock").id,
                    "location": self.Not("deleted"),
                }
            )

            primers = sess.Sample.last(
                4, query={"sample_type_id": sess.SampleType.find_by_name("Primer").id}
            )

            fragments = sess.Sample.last(
                4, query={"sample_type_id": sess.SampleType.find_by_name("Fragment").id}
            )

            plasmids = sess.Sample.last(
                3, query={"sample_type_id": sess.SampleType.find_by_name("Plasmid").id}
            )

            subchain = [
                "Make PCR Fragment",
                "Run Gel",
                "Extract Gel Slice",
                "Purify Gel Slice",
            ]

            ops1 = canvas.chain(*(subchain + ["Assemble Plasmid"]))
            ops2 = canvas.chain(*(subchain + ops1[-1:]))

            ops3 = canvas.chain(*(subchain + ["Assemble Plasmid"]))
            ops4 = canvas.chain(*(subchain + ops3[-1:]))

            ops5 = canvas.chain(*(subchain + ["Assemble Plasmid"]))
            ops6 = canvas.chain(*(subchain + ops5[-1:]))
            ops7 = canvas.chain(*(subchain + ops5[-1:]))
            ops8 = canvas.chain(*(subchain + ops5[-1:]))
            ops9 = canvas.chain(*(subchain + ops5[-1:]))

            for op in canvas.get_op_by_name("Run Gel"):
                pour_gel = canvas.chain("Pour Gel", op)[0]

            # pour_gels = [op for op in canvas.operations if
            #              op.operation_type.name == 'Pour Gel']
            # print([op.outputs[0].sample for op in pour_gels])

            # chain1 using primer1
            canvas.set_field_value_and_propogate(
                ops1[0].outputs[0], sample=fragments[0]
            )
            # chain2 using primer2
            canvas.set_field_value_and_propogate(
                ops2[0].outputs[0], sample=fragments[1]
            )

            # chain3 using primer2
            canvas.set_field_value_and_propogate(
                ops3[0].outputs[0], sample=fragments[1]
            )
            # chain4 using primer1
            canvas.set_field_value_and_propogate(
                ops4[0].outputs[0], sample=fragments[0]
            )

            canvas.set_field_value_and_propogate(
                ops6[0].outputs[0], sample=fragments[1]
            )
            canvas.set_field_value_and_propogate(
                ops7[0].outputs[0], sample=fragments[1]
            )

            def pcr(op, p1, p2, t):
                canvas.set_field_value(op.input("Forward Primer"), sample=p1)
                canvas.set_field_value(op.input("Reverse Primer"), sample=p2)
                canvas.set_field_value(op.input("Template"), sample=t)

            pcr(ops1[0], primers[0], primers[1], plasmids[0])
            pcr(ops2[0], primers[2], primers[3], plasmids[1])
            pcr(ops4[0], primers[0], primers[1], plasmids[0])
            pcr(ops3[0], primers[2], primers[3], plasmids[1])

            canvas.set_field_value(ops1[-1].outputs[0], sample=plasmids[2])
            canvas.set_field_value(ops3[-1].outputs[0], sample=plasmids[2])

            op_types = sorted([op.operation_type.name for op in canvas.operations])
            print(op_types)

            canvas.optimize(merge_missing_samples=True)

            canvas.prettify()
            canvas.save()
            canvas.open()

            op_types = sorted([op.operation_type.name for op in canvas.operations])
            print(op_types)
            assert len(canvas.get_op_by_name("Assemble Plasmid")) == 2
            assert len(canvas.get_op_by_name("Pour Gel")) == 6

            for op in canvas.get_op_by_name("Assemble Plasmid"):
                # assert len({fv.child_sample_id for fv in op.inputs}) == 2
                assert len(op.inputs) in [4, 2]

                for input_fv in op.inputs:
                    assert len(canvas.get_incoming_wires(input_fv)) == 1

            assert len(canvas.get_op_by_name("Pour Gel")) == 2

    def test_optimize_with_existing_plan(self, session):

        with session.with_cache() as sess:
            canvas = Planner(sess)

            q = self.sql(
                {
                    "object_type_id": sess.ObjectType.find_by_name(
                        "E coli Plate of Plasmid"
                    ).id,
                    "location": self.Not("deleted"),
                }
            )
            item = sess.Item.one(query=q)
            assert item

            chain = [
                "Check Plate",
                "Make Overnight Suspension",
                "Make Miniprep",
                "Yeast Transformation",
                "Yeast Overnight Suspension",
            ]

            ops = canvas.chain(*chain)
            canvas.set_field_value_and_propogate(ops[0].inputs[0], sample=item.sample)
            canvas.set_to_available_item(ops[0].inputs[0])

            ops = canvas.chain(*chain)
            canvas.set_field_value_and_propogate(ops[0].inputs[0], sample=item.sample)
            canvas.set_to_available_item(ops[0].inputs[0])

            assert len(canvas.plan.operations) == 10
            canvas.save()

        plan_id = canvas.plan.id
        with session.with_cache(timeout=60) as sess:
            canvas = Planner(sess.Plan.find(plan_id))
            canvas.optimize()
            assert len(canvas.plan.operations) == 7
