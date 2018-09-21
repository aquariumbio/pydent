def test_return_none(session):
    s = session.Sample.find(12397958739)
    assert s is None