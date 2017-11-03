import pytest
from pydent.aq import AqSession


def test_login(load_session, config):
    s = AqSession()
    AqSession().nursery
    with pytest.raises(AttributeError):
        AqSession().AqHTTPThatDoesntExist

    # Make sure AqHTTP is equal to the name in the config file
    AqHTTP_names = list(config.keys())
    assert AqSession().session_name == AqHTTP_names[-1]


def test_AqHTTP_close(config):
    # Close AqHTTP
    AqSession().close()
    assert AqSession().session is None

    # Set AqHTTP to last AqHTTP in secrets/config.json
    AqSession().set(list(config.keys())[-1])
    assert AqSession().session is not None
