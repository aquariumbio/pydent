import pytest
from pydent.models import *
from pydent import AqSession
import requests


def data():
    {
        "AllowableFieldType": [
            {
            "id": 3,
            "field_type_id": 1,
            "object_type_id": 2,
            "sample_type_id": 3
            }
        ],
        "FieldType": [

        ]
    }


@pytest.fixture(scope="function")
def test_something(monkeypatch, mock_post):

    # Create a mock session
    monkeypatch.setattr(requests, "post", mock_post)
    aquarium_url = "http://52.52.525.52"
    session = AqSession("username", "password", aquarium_url)
    return session