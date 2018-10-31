import os

import pytest
import vcr

from pydent import AqSession


###########
# VCR setup
###########


# TODO: tests: completly deterministic tests
# TODO: tests: parameter or config file for recording mode
# TODO: tests: ignore header in vcr recordings

def hash_response(r):
    """Hash function for request matcher. Defines what vcr will consider
    to be the same request."""
    return "{}:{}:{}".format(r.method, r.uri, r.body)


def hash_test_function(func):
    """Hashes a pytest test function to a unique file name based on
    its class, module, and name"""
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
    """Request matcher. Defines what vcr considers the same request"""
    return hash_response(r1) == hash_response(r2)


myvcr = vcr.VCR()
myvcr.register_matcher('matcher', matcher)
myvcr.match_on = ['matcher']
myvcr.record_mode = "new_episodes"
here = os.path.abspath(os.path.dirname(__file__))
fixtures_path = os.path.join(here, "fixtures/vcr_cassettes")


############
# Test hooks
############

@pytest.hookimpl(hookwrapper=True)
def pytest_pyfunc_call(pyfuncitem):
    """Sorts through each test, uses a vcr cassette to run the test, storing the
    request results into a single file location"""
    cassette_name = hash_test_function(pyfuncitem)
    with myvcr.use_cassette(os.path.join(fixtures_path, cassette_name) + ".yaml"):
        outcome = yield


###########
# Fixtures
###########

@pytest.fixture(scope="session")
def session(config):
    """
    Returns a live aquarium connection.
    """
    return AqSession(**config)
