def test_logging(fake_session):
    fake_session.set_verbose(True)
    fake_session.utils.aqhttp._info("This is a logged message. This is hard to assert...")