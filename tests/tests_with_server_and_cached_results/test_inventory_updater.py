def test_inventory_updater(session):
    ot = session.ObjectType.one(query="rows > 2 AND columns > 2")
    collection = session.Collection.new(object_type=ot)

    primer = session.SampleType.find_by_name("Primer")
    fragment = session.SampleType.find_by_name("Fragment")
    plasmid = session.SampleType.find_by_name("Plasmid")
    yeast = session.SampleType.find_by_name("Yeast Strain")

    item = session.Item.new(
        object_type=session.ObjectType.find_by_name("Fragment Stock"),
        sample=collection.sample_matrix[0, 0],
    )

    planner = Planner(session)
    op = planner.create_operation_by_name("Make PCR Fragment")
    planner.set_field_value(op.input("Template"), item=item)
    g = models_to_graph(session, [planner.plan])
