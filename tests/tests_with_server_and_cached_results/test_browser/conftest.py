import pytest

import json
import os

here = os.path.abspath(os.path.dirname(__file__))


@pytest.fixture(scope="function")
def example_fragment(fake_session):
    with open(os.path.join(here, "example_fragment.json"), "r") as f:
        data = json.load(f)
    return fake_session.Sample.load(data)
