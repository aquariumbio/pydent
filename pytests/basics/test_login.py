import pytest
from pydent import AqSession
from pydent.exceptions import TridentLoginError, TridentRequestError


def test_login(session):
    u = session.User.find(1)
    print(type(u))


def test_raise_error_with_incorrect_url():
    with pytest.raises(TridentLoginError):
        AqSession("john", "johnspassword", "52534.32.43.4")


def test_raise_error_with_incorrect_login():
    s = AqSession("john", "johnspassword", "http://52.27.43.242:81/")
    with pytest.raises(TridentRequestError):
        s.User.find(1)


# def test_login(load_session, config):
#     s = AqSession()
#     AqSession().nursery
#     with pytest.raises(AttributeError):
#         AqSession().AqHTTPThatDoesntExist
#
#     # Make sure AqHTTP is equal to the name in the config file
#     AqHTTP_names = list(config.keys())
#     assert AqSession().session_name == AqHTTP_names[-1]
#
#
# def test_AqHTTP_close(config):
#     # Close AqHTTP
#     AqSession().close()
#     assert AqSession().session is None
#
#     # Set AqHTTP to last AqHTTP in secrets/config.json
#     AqSession().set(list(config.keys())[-1])
#     assert AqSession().session is not None
