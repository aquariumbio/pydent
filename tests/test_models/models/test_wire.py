from pydent.models import Wire, FieldValue


def test_constructor():
    fvin = FieldValue(name="input")
    fvout = FieldValue(name="output")
    w = Wire(
        source=fvin,
        destination=fvout
    )
    w.print(relations={"source", "destination"})
    assert w.to_save_json() == {
            "from": fvin.dump(),
            "to": fvout.dump(),
            'rid': w.rid
    }