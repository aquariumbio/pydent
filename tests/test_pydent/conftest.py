import json
import os

import pytest
import requests

from pydent.aqsession import AqSession


@pytest.fixture(scope="session")
def mock_login_post():
    """
    A fake cookie to fake a logged in account
    """

    def fake_post(path, **kwargs):
        routes = {
            "sessions.json": dict(
                cookies={
                    "remember_token_NURSERY_production": "SLLRrvtYchvNLhWHJR3FVg; path=/; expires=Tue, 10-Nov"
                                                         "-2037 00:15:54 GMT, XSRF-TOKEN=tlhdb%2BXY1FVupNSe0GdOvzNNFULtwW4Xzfkiya5gAbU%3D; pat"
                                                         "h=/, _aquarium_NURSERY_production_session=dfsdf"
                                                         "VwTlNlMEdkT3Z6Tk5GVUx0d1c0WHpsdfsma2l5YTVnQWJVPQY6BkVGSSIKZmxhc2gGOwZUbzolQWN0aW9uRGlzcG"
                                                         "F0Y2g6OkZsYXNoOjpGbGFzaEhhc2gJOgpAdXNsdfsdfsMmY4NDliMDY1MWJiOGVlNzJlZTlm"
                                                         "NjJlZjU1NmQ4YWQGOwZU-"
                                                         "-9e441bf82be44d39e7ec95f475b02751bb7b3c46; path=/; HttpOnly"
                }
            )
        }
        for key, res in routes.items():
            if key in path:
                response = requests.Response()
                response.__dict__.update(res)
                return response

    return fake_post


@pytest.fixture(scope="function")
def fake_session(monkeypatch, mock_login_post):
    """
    Returns a fake session using a fake cookie
    """
    monkeypatch.setattr(requests, "post", mock_login_post)
    aquarium_url = "http://52.52.525.52"
    session = AqSession("username", "password", aquarium_url)
    return session


@pytest.fixture(scope="function")
def fake_response():
    class FakeRequest(object):
        def __init__(self, status_code=200, url="myfakeurl.com", method="post"):
            self.status_code = status_code
            self.url = url
            self.method = method
            self.body = {}

    class FakeResponse(requests.Response):

        def __init__(self, method, url, body, status_code):
            self.status_code = status_code
            self.request = FakeRequest(status_code=status_code, url=url, method=method)
            self.body = body

        def json(self):
            return json.load(self.body)

    def make_response(method, url, body, status_code):
        response = requests.Response()
        response.body = body
        response.json = lambda: body
        response.status_code = status_code
        response.request = FakeRequest(status_code=status_code, url=url, method=method)
        return response

    return make_response


@pytest.fixture(autouse=True)
def no_requests(monkeypatch):
    def dummy(*args, **kwargs):
        return None
        raise Exception("Requests are disabled in {}".format(os.path.abspath(__file__)))
    monkeypatch.setattr("requests.sessions.Session.request", dummy)
