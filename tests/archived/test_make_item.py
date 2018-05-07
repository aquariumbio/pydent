from pydent import models


def test_make_item(session):
    st = session.SampleType.find_by_name("Fragment")
    s = st.samples[-10]
    ot = session.ObjectType.find_by_name("Fragment Stock")
    i = models.Item(sample_id=s.id, object_type_id=ot.id)
    i.connect_to_session(session)
    i.make()
    i.print()
