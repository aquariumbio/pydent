import pytest
from pydent.session import AqHTTP, AqSession, ModelInterface, UtilityInterface
from pydent.base import ModelRegistry
import requests


def test_session(monkeypatch, mock_post):
    """Test creating a session using fake login information."""

    monkeypatch.setattr(requests, "post", mock_post)
    aquarium_url = "http://52.52.525.52"
    session = AqSession("username", "password", aquarium_url)
    assert isinstance(session._AqSession__aqhttp, AqHTTP)


def test_access_interface(monkeypatch, mock_post):
    """Test accessibility of model interfaces"""

    monkeypatch.setattr(requests, "post", mock_post)
    aquarium_url = "http://52.52.525.52"
    session = AqSession("username", "password", aquarium_url)

    # model interfaces
    for model_name, model in ModelRegistry.models.items():
        interface = getattr(session, model_name)
        assert isinstance(interface, ModelInterface)


def test_access_utils_interface(monkeypatch, mock_post):
    """Test accesibility of create interface"""

    monkeypatch.setattr(requests, "post", mock_post)
    aquarium_url = "http://52.52.525.52"
    session = AqSession("username", "password", aquarium_url)

    # create interface
    assert isinstance(getattr(session, UtilityInterface.__name__), UtilityInterface)

