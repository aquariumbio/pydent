def test_new(session):

    user = session.User.new()
    assert user.session is not None