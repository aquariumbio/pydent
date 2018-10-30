import pytest
from pydent import AqSession


@pytest.fixture(scope="session")
def session(config):
    """
    Returns a live aquarium connection.
    """
    session = AqSession(**config)
    # session.set_timeout(30)
    return session