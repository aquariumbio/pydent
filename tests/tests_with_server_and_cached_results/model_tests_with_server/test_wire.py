def test_wire_create_and_dump(session):

    fvs = session.FieldValue.last(2)

    session.Wire.first()

    w = session.Wire(source=fvs[0], destination=fvs[1])

    wire_data = w.dump()

    assert 'from_id' in wire_data
    assert 'to_id' in wire_data

    assert w.source
    assert w.destination

    assert getattr(w, 'from')
    assert getattr(w, 'to')

    assert w.from_id == fvs[0].id
    assert w.to_id == fvs[1].id


def test_wire_create_and_dump_with_new_field_value(session):

    field_type = session.FieldType.one(query={'parent_class': 'Operation'})

    w = session.Wire(source=session.FieldValue.new(field_type=field_type), destination=session.FieldValue.new(field_type=field_type))

    wire_data = w.dump()

    assert 'from_id' in wire_data
    assert 'to_id' in wire_data

    assert w.source
    assert w.destination

    assert w.from_id is None
    assert w.to_id is None
