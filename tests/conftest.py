import json
import os

import pytest
import requests

from pydent.session import AqSession


@pytest.fixture(scope="session")
def config():
    dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(dir, "secrets", "config.json.secret")
    config = None
    with open(config_path, 'rU') as f:
        config = json.load(f)
    return config


@pytest.fixture(scope="session")
def session():
    return AqSession(**config())


@pytest.fixture(scope="session")
def mock_login_post():
    """A fake cookie to fake a logged in account"""

    def post(path, **kwargs):
        routes = {
            "sessions.json": dict(
                headers={
                    'set-cookie': "remember_token_NURSERY_production=SLLRrvtYchvNLhWHJR3FVg; path=/; expires=Tue, 10-Nov"
                                  "-2037 00:15:54 GMT, XSRF-TOKEN=tlhdb%2BXY1FVupNSe0GdOvzNNFULtwW4Xzfkiya5gAbU%3D; pat"
                                  "h=/, _aquarium_NURSERY_production_session=dfsdf"
                                  "VwTlNlMEdkT3Z6Tk5GVUx0d1c0WHpsdfsma2l5YTVnQWJVPQY6BkVGSSIKZmxhc2gGOwZUbzolQWN0aW9uRGlzcG"
                                  "F0Y2g6OkZsYXNoOjpGbGFzaEhhc2gJOgpAdXNsdfsdfsMmY4NDliMDY1MWJiOGVlNzJlZTlm"
                                  "NjJlZjU1NmQ4YWQGOwZU-"
                                  "-9e441bf82be44d39e7ec95f475b02751bb7b3c46; path=/; HttpOnly"}
            )
        }
        for key, res in routes.items():
            if key in path:
                response = requests.Response()
                response.__dict__.update(res)
                return response

    return post


@pytest.fixture(scope="function")
def fake_session(monkeypatch, mock_login_post):
    monkeypatch.setattr(requests, "post", mock_login_post)
    aquarium_url = "http://52.52.525.52"
    session = AqSession("username", "password", aquarium_url)
    return session

    # # Uncomment the following code to turn off requests
    # import pytest
    # @pytest.fixture(autouse=True)
    # def no_requests(monkeypatch):
    #     monkeypatch.delattr("requests.sessions.Session.request")
