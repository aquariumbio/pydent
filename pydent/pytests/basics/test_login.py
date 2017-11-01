import pytest
from pydent.aq import *

def test_login(load_session, config):
    s = Session()
    Session().nursery
    with pytest.raises(AttributeError):
        Session().AqHTTPThatDoesntExist

    # Make sure AqHTTP is equal to the name in the config file
    AqHTTP_names = list(config.keys())
    assert Session().session_name == AqHTTP_names[-1]

def test_AqHTTP_close(config):
    # Close AqHTTP
    Session().close()
    assert Session().session is None

    # Set AqHTTP to last AqHTTP in secrets/config.json
    Session().set(list(config.keys())[-1])
    assert Session().session is not None