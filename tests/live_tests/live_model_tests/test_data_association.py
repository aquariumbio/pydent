from uuid import uuid4


def test_data_association(session):

    sample = session.Sample.find_by_name("DummyPlasmid")
    item = sample.items[0]

    val = str(uuid4())
    item.associate('myval', val)

    da = item.data_associations[-1]
    assert da.value == val

    reloaded = session.Item.find(item.id)
    assert reloaded.data_associations[-1].value == val

    print(reloaded.get("myval"))