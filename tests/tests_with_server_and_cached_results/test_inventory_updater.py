from uuid import uuid4

from pydent import save_inventory
from pydent.planner import Planner


def test_inventory_updater(session):
    ot = session.ObjectType.one(query="rows > 2 AND columns > 2")
    collection = session.Collection.new(object_type=ot)

    primer = session.SampleType.find_by_name("Primer")
    fragment = session.SampleType.find_by_name("Fragment")
    plasmid = session.SampleType.find_by_name("Plasmid")
    yeast = session.SampleType.find_by_name("Yeast Strain")

    frag = fragment.new_sample(
        str(uuid4()),
        project="test",
        description="",
        properties={
            "Forward Primer": primer.new_sample(
                str(uuid4()),
                project="test",
                description="",
                properties={"Anneal Sequence": "AGGGATAT", "T Anneal": 50},
            ),
            "Length": 1000,
            "Sequence": "",
        },
    )

    collection[0, 0] = frag

    item = session.Item.new(
        object_type=session.ObjectType.find_by_name("Fragment Stock"),
        sample=collection.sample_matrix[0, 0],
    )

    print(item.object_type)

    planner = Planner(session)
    op = planner.create_operation_by_name("Make PCR Fragment")
    planner.set_field_value(op.input("Template"), item=item)

    saved = save_inventory(session, [planner.plan, collection])

    # assert frag in saved
    assert frag.id
    assert frag.properties["Forward Primer"].id
    assert item.id
    assert planner.plan.id
    assert collection.id

    save_inventory(session, [planner.plan, collection], merge_samples=True)
