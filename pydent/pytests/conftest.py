import pytest
import os
import json
from pydent.aq import AqSession


@pytest.fixture(scope="module")
def config_path():
    folder = os.path.dirname(os.path.abspath(__file__))
    rel_loc = "secrets/config.json"
    return os.path.join(folder, rel_loc)

@pytest.fixture(scope="module")
def config():
    with open(os.path.abspath(config_path())) as f:
        return json.load(f)

@pytest.fixture(scope="module")
def load_session():
    AqSession().create_from_config_file(config_path())
    return 5

