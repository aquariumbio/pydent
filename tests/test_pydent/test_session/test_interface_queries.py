import pytest
import requests

from pydent import AqSession
from pydent.aqhttp import AqHTTP
from pydent.exceptions import TridentRequestError


def test_where_queries_should_return_empty_array(monkeypatch, mock_login_post):
    """Empty where queries should return empty arrays.

    Here, we replaces AqHTTP.post with a mock post that returns an empty
    array.
    """

    # Create a mock session
    monkeypatch.setattr(requests, "post", mock_login_post)
    aquarium_url = "http://52.52.525.52"
    session = AqSession("username", "password", aquarium_url)

    def mock_post(*args, **kwargs):
        return []

    monkeypatch.setattr(AqHTTP, "post", mock_post)

    samples = session.SampleType.where({"id": 3454345, "object_type_id": 23432})

    assert samples == [], "Where should return an empty list"


def test_find_query_returns_none(monkeypatch, mock_login_post):
    """Empty find queries should return None.

    Here, we replace the AqHTTP.post with a mock post, that has an error
    code 422 (which is thrown by Aquarium in cases where it cannot find
    the model).
    """

    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

    # Create a mock session
    monkeypatch.setattr(requests, "post", mock_login_post)
    aquarium_url = "http://52.52.525.52"
    session = AqSession("username", "password", aquarium_url)

    def mock_post(*args, **kwargs):
        raise TridentRequestError("There was an error", MockResponse({}, 422))

    monkeypatch.setattr(AqHTTP, "post", mock_post)

    sample = session.SampleType.find(2342342)

    assert sample is None


def find_with_none_raises_value_error(fake_session):
    invalid_ids = [None, "1"]
    for invalid_id in invalid_ids:
        with pytest.raises(ValueError):
            fake_session.Sample.find(invalid_id)


def find_by_name_with_invalid_raises_value_error(fake_session):
    invalid_names = [None, 1]
    for invalid_name in invalid_names:
        with pytest.raises(ValueError):
            fake_session.Sample.find_by_name(invalid_name)
