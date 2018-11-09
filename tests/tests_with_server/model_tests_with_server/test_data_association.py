from uuid import uuid4


def test_data_association(session):

    sample = session.Sample.find_by_name("DummyPlasmid")
    item = sample.items[0]

    val = str(uuid4())

    print(len(item.data_associations))
    _da = item.associate('myval', val)
    print(_da)
    da = item.data_associations[-1]
    for d in item.data_associations[-10:]:
        print(d)
    print(len(item.data_associations))
    print(da)
    print(da.value)
    print(val)
    assert da.value == val

    reloaded = session.Item.find(item.id)
    print(len(reloaded.data_associations))
    print(reloaded.get("myval"))
    assert reloaded.data_associations[-1].value == val