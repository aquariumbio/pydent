from pydent.models import Wire, FieldValue


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
            "from": fvin.dump(),
            "to": fvout.dump(),
            'rid': w.rid,
            "active": True,
            'id': None
    }

