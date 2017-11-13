"""

This module contains tests using mock requests.

"""

import requests
import pytest
from pydent.session import AqHTTP
from pydent.exceptions import TridentLoginError, TridentTimeoutError


def test_login(monkeypatch, mock_post):
    """Simulates an Aquarium login using a pretend cookie. AqHTTP should instantiate with no errors."""
    aquarium_url = "http://52.45.55.456:58/"
    monkeypatch.setattr(requests, "post", mock_post)
    http = AqHTTP("username", "password", aquarium_url)
    assert http.aquarium_url == aquarium_url
    assert http.login == "username"
    assert not hasattr(http, "password")


def test_login_bad_url(monkeypatch):
    """Simulates an Aquarium login using a bad url. Should raise a login error."""

    aquarium_url = "This is a bad url"
    with pytest.raises(TridentLoginError):
        AqHTTP("username", "password", aquarium_url)


def test_login_wrong_url(monkeypatch):
    """Simulates an Aquarium login using a bad url. Should raise a timeout error."""

    aquarium_url = "http://52.52.52.52:81/"
    monkeypatch.setattr(AqHTTP, "TIMEOUT", 0.01)
    with pytest.raises(TridentTimeoutError):
        AqHTTP("username", "password", aquarium_url)


def test_login_no_cookie(monkeypatch):
    """Should raise LoginError if cookie is not found."""

    def mock_post(path, **kwargs):
        routes = {
            "sessions.json": {}
        }
        for key, res in routes.items():
            if key in path:
                response = requests.Response()
                response.__dict__.update(res)
                return response

    aquarium_url = "http://52.45.55.456:58/"
    monkeypatch.setattr(requests, 'post', mock_post)
    with pytest.raises(TridentLoginError):
        AqHTTP("username", "password", aquarium_url)