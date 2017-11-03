import os
import json
import pytest
from aq import Session


@pytest.fixture(scope="module")
def config_path():
    folder = "pydent/pytests"
    rel_loc = "secrets/config.json"
    return os.path.join(folder, rel_loc)

@pytest.fixture(scope="module")
def config():
    with open(os.path.abspath(config_path())) as f:
        return json.load(f)

@pytest.fixture(scope="module")
def load_session():
    Session.create_from_config_file(config_path())
    return 5

