def test_constructor(fake_session):
    fvin = fake_session.FieldValue(name="input")
    fvout = fake_session.FieldValue(name="output")
    w = fake_session.Wire(
        source=fvin,
        destination=fvout
    )
    w.print()

    assert w.to
    assert getattr(w, 'from')
    assert w.source
    assert w.destination

    assert w.to_save_json() == {
            "from": {"rid": fvin.rid},
            "to": {"rid": fvout.rid},
            "from_id": fvin.id,
            "to_id": fvout.id,
            "active": True,
            'id': None
    }