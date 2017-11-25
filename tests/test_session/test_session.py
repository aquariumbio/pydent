import warnings

import pytest
import requests

from pydent.base import ModelRegistry
from pydent.session import AqHTTP, AqSession, ModelInterface, UtilityInterface
from pydent.models import User

@pytest.fixture(scope="function")
def aqsession(monkeypatch, mock_post):
    monkeypatch.setattr(requests, "post", mock_post)
    aquarium_url = "http://52.52.525.52"
    session = AqSession("username", "password", aquarium_url)
    return session


def test_session_models(aqsession):
    assert aqsession.models == list(ModelRegistry.models.keys())


def test_session_repr(aqsession):
    repr = str(aqsession)


def test_interactive_login():
    warnings.warn("No test implemented for interactive login...")
    # I don't know how to test interactive inputs...


def test_access_models_interface(aqsession):
    """Test accessibility of model interfaces"""

    # model interfaces
    for model_name, model in ModelRegistry.models.items():
        interface = getattr(aqsession, model_name)
        assert isinstance(interface, ModelInterface)


def test_access_utils_interface(aqsession):
    """Test accesibility of create interface"""

    # create interface
    assert isinstance(getattr(aqsession, UtilityInterface.__name__), UtilityInterface)


# TODO: this is all muddled with models!
def test_current_user(monkeypatch, aqsession):

    def fake_post(*args, **kwargs):
        return [{
            "login": "mylogin",
            "id": 1,
            "name": "Jane Doe"
        }]

    monkeypatch.setattr(AqHTTP, 'post', fake_post)

    user = aqsession.current_user
    assert isinstance(user, User)


# TODO: this is all muddled with models!
def test_not_logged_in(monkeypatch, aqsession):

    def fake_post(*args, **kwargs):
        return []

    monkeypatch.setattr(AqHTTP, 'post', fake_post)
    assert not aqsession.logged_in()

def test_logged_in(monkeypatch, aqsession):

    def fake_post(*args, **kwargs):
        return [{
            "login": "mylogin",
            "id": 1,
            "name": "Jane Doe"
        }]

    monkeypatch.setattr(AqHTTP, 'post', fake_post)
    assert aqsession.logged_in()

def test_set_timeout(aqsession):

    aqsession.set_timeout(5)
    assert aqsession._AqSession__aqhttp.timeout == 5

