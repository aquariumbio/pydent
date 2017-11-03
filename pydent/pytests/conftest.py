import pytest
import os
import json
from pydent.aq import AqSession


@pytest.fixture(scope="module")
def config_path():
    """
    Returns the path to the configuration file.
    """
    folder = os.path.dirname(os.path.abspath(__file__))
    rel_loc = "secrets/config.json"
    return os.path.join(folder, rel_loc)


@pytest.fixture(scope="module")
def config():
    """
    Returns the configuration file contents.
    """
    with open(os.path.abspath(config_path())) as config_file:
        return json.load(config_file)


@pytest.fixture(scope="module")
def load_session():
    """
    Creates a session from the configuration.
    """
    AqSession().create_from_config_file(config_path())
    return 5
