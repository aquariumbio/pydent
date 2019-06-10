
from pydent.base import ModelRegistry
from pydent.aqhttp import AqHTTP
from pydent.interfaces import QueryInterface, UtilityInterface
from pydent.models import User
from pydent.models import __all__ as all_models


def test_session_models(fake_session):
    assert fake_session.models == list(ModelRegistry.models.keys())


def test_session_repr(fake_session):
    repr = str(fake_session)
    assert repr


def test_access_models_interface(fake_session):
    """Test accessibility of model interfaces"""

    # model interfaces
    for model_name in all_models:
        interface = getattr(fake_session, model_name)
        assert isinstance(interface, QueryInterface)


def test_access_utils_interface(fake_session):
    """
    Test accessibility of create interface
    """

    # create interface
    assert isinstance(fake_session.utils, UtilityInterface)


# TODO: this is all muddled with models!
def test_current_user(monkeypatch, fake_session):

    def fake_post(*args, **kwargs):
        return [{
            "login": "mylogin",
            "id": 1,
            "name": "Jane Doe"
        }]

    monkeypatch.setattr(AqHTTP, 'post', fake_post)

    user = fake_session.current_user
    assert isinstance(user, User)


# TODO: this is all muddled with models!
def test_not_logged_in(monkeypatch, fake_session):

    def fake_post(*args, **kwargs):
        return []

    monkeypatch.setattr(AqHTTP, 'post', fake_post)
    assert not fake_session.logged_in()


def test_logged_in(monkeypatch, fake_session):

    def fake_post(*args, **kwargs):
        return [{
            "login": "mylogin",
            "id": 1,
            "name": "Jane Doe"
        }]

    monkeypatch.setattr(AqHTTP, 'post', fake_post)
    assert fake_session.logged_in()


def test_set_timeout(fake_session):

    fake_session.set_timeout(5)
    assert fake_session._aqhttp.timeout == 5
