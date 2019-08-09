def test_find_id_0(session):
    s = session()
    assert s.Plan.find(0) is None


def test_find_id_0(session):
    s = session.with_cache()
    assert s.Plan.find(0) is None
