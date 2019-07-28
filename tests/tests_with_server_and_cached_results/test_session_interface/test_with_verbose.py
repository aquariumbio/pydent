def test_verbose_on(session):

    with session(using_verbose=True) as sess:
        sess.Sample.one()


def test_verbose_off(session):

    with session(using_verbose=False) as sess:
        sess.Sample.one()


def test_verbose_inherit(session):

    sess = session(using_verbose=True)
    with sess() as sess2:
        sess2.Sample.one()
