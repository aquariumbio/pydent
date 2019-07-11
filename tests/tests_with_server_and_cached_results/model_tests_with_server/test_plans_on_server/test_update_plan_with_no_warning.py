def test_no_warning(session):
    session.Plan.one().update()