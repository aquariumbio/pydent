from pydent import models


def test_create_item(session):
    st = session.SampleType.find_by_name("Fragment")
    s = st.samples[-10]
    ot = session.ObjectType.find_by_name("Fragment Stock")
    i = session.Item.new(sample_id=s.id, object_type_id=ot.id)
    i.create()
    assert i.id


def test_save_item(session):
    st = session.SampleType.find_by_name("Fragment")
    s = st.samples[-10]
    ot = session.ObjectType.find_by_name("Fragment Stock")
    i = session.Item.new(sample_id=s.id, object_type_id=ot.id)
    i.save()
    assert i.id


def test_save_item(session):
    st = session.SampleType.find_by_name("Fragment")
    s = st.samples[-10]
    ot = session.ObjectType.find_by_name("Fragment Stock")
    i = session.Item.new(sample_id=s.id, object_type_id=ot.id)
    i.save()
    id1 = i.id

    i.save()

    assert i.id == id1


def test_update_item_location(session):
    st = session.SampleType.find_by_name("Fragment")
    s = st.samples[-10]
    ot = session.ObjectType.find_by_name("Fragment Stock")
    i = session.Item.new(sample_id=s.id, object_type_id=ot.id)
    i.save()
    print(i.raw)
    assert i.id
    i.location = "tabletop"
    i.save()
    loaded = session.Item.find(i.id)
    assert loaded.location == "tabletop"
