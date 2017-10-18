import pytest
from pydent import *

def test_login(load_session, config):
    s = Session
    Session.Nursery
    with pytest.raises(AttributeError):
        Session.SessionThatDoesntExist

    # Make sure session is equal to the name in the config file
    session_names = list(config.keys())
    assert Session.session_name() == session_names[-1]

def test_session_close(config):
    # Close session
    Session.close()
    assert Session.session is None

    # Set session to last session in secrets/config.json
    Session.set(list(config.keys())[-1])
    assert Session.session is not None

def test_sample_type_all():
    SampleType.all()