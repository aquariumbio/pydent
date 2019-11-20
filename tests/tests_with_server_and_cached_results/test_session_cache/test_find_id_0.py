def test_find_id_0(session):
    s = session()
    plan = s.Plan.find(0)
