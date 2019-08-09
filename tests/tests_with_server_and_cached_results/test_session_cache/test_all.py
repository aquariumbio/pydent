def test_all(session):
    all_ots = session.ObjectType.all()
    s = session.with_cache()

    ot = s.ObjectType.one()

    s.ObjectType.all()
    ots = s.browser.model_cache["ObjectType"].values()
    assert len(ots) == len(all_ots)
    assert ot in ots
