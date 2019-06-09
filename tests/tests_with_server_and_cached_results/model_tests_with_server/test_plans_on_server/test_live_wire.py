def test_wire_create_and_dump(session):

    output_fv = session.FieldValue.one(query={'role': 'output'})
    input_fv = session.FieldValue.one(query={'role': 'input'})

    session.Wire.first()

    w = session.Wire(source=output_fv, destination=input_fv)

    wire_data = w.dump()

    assert 'from_id' in wire_data
    assert 'to_id' in wire_data

    assert w.source
    assert w.destination

    assert w.from_id == output_fv.id
    assert w.to_id == input_fv.id


def test_wire_create_and_dump_with_new_field_value(session):

    output_field_type = session.FieldType.one(query={'parent_class': 'OperationType', 'role': 'output'})
    input_field_type = session.FieldType.one(query={'parent_class': 'OperationType', 'role': 'input'})
    assert output_field_type
    assert input_field_type

    w = session.Wire(
        source=session.FieldValue.new(field_type=output_field_type),
        destination=session.FieldValue.new(field_type=input_field_type))

    wire_data = w.dump()

    assert 'from_id' in wire_data
    assert 'to_id' in wire_data

    assert w.source
    assert w.destination

    assert w.from_id is None
    assert w.to_id is None
