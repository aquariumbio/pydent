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


# TODO: somehow moving Items doesn't work...
def test_move(session):
    st = session.SampleType.find_by_name("Fragment")
    s = st.samples[-10]
    ot = session.ObjectType.find_by_name("Fragment Stock")
    i = session.Item.new(sample_id=s.id, object_type_id=ot.id)
    i.save()
    assert i.id
    i.move("tabletop")

    loaded = session.Item.find(i.id)
    assert loaded.location == "tabletop"
