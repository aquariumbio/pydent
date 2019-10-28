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

    def test_optimize_plan(self, session):

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

            canvas.optimize_plan()

            assert len(canvas.plan.operations) == 5

    def test_optimize_plan2(self, session):

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

            canvas.optimize_plan()

            assert len(canvas.plan.operations) == 7
