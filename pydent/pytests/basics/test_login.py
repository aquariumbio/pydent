import pytest
from pydent.aq import *

def test_login(load_session, config):
    s = AqHTTP
    AqHTTP.Nursery
    with pytest.raises(AttributeError):
        AqHTTP.AqHTTPThatDoesntExist

    # Make sure AqHTTP is equal to the name in the config file
    AqHTTP_names = list(config.keys())
    assert AqHTTP.session_name() == AqHTTP_names[-1]

def test_AqHTTP_close(config):
    # Close AqHTTP
    AqHTTP.close()
    assert AqHTTP.session is None

    # Set AqHTTP to last AqHTTP in secrets/config.json
    AqHTTP.set(list(config.keys())[-1])
    assert AqHTTP.session is not None