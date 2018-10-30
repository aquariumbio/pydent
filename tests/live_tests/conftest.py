import os

import pytest
import vcr

from pydent import AqSession


####################
# Requests Recording
####################

def hash_response(r):
    """Hashes a request into a unique name"""
    return "{}:{}:{}".format(r.method, r.uri, r.body)

def hash_test_function(func):
    if func.cls:
        cls = func.cls.__name__
    else:
        cls = "None"
    return "{module}_{cls}_{name}".format(
        module=func.module.__name__,
        cls=cls,
        name=func.name,
    )

def matcher(r1, r2):
    return hash_response(r1) == hash_response(r2)

myvcr = vcr.VCR()
myvcr.register_matcher('matcher', matcher)
myvcr.match_on = ['matcher']
myvcr.record_mode = "new_episodes"
here = os.path.abspath(os.path.dirname(__file__))
fixtures_path = os.path.join(here, "fixtures/vcr_cassettes")


@pytest.hookimpl(hookwrapper=True)
def pytest_pyfunc_call(pyfuncitem):
    cassette_name = hash_test_function(pyfuncitem)
    with myvcr.use_cassette(os.path.join(fixtures_path, cassette_name) + ".yaml"):
        outcome = yield


@pytest.fixture(scope="session")
def session(config):
    """
    Returns a live aquarium connection.
    """
    session = AqSession(**config)
    return session
