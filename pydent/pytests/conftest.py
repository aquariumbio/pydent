import pytest
import os
import json
from pydent import Session


@pytest.fixture(scope="module")
def config_path():
    return "secrets/config.json"

@pytest.fixture(scope="module")
def config():
    with open(os.path.abspath(config_path())) as f:
        return json.load(f)

@pytest.fixture(scope="module")
def load_session():
    Session.create_from_config_file(config_path())
    return 5