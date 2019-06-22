import json
import os

import pytest
import vcr

from pydent import AqSession


###########
# VCR setup
###########


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
        module=func.module.__name__, cls=cls, name=func.name
    )


def matcher(r1, r2):
    """Request matcher. Defines what vcr considers the same request"""
    return hash_response(r1) == hash_response(r2)


############
# Test hooks
############

# https://vcrpy.readthedocs.io/en/latest/usage.html
myvcr = vcr.VCR()
myvcr.register_matcher("matcher", matcher)
myvcr.match_on = ["matcher"]
# record mode is handled in pytest.ini
here = os.path.abspath(os.path.dirname(__file__))
fixtures_path = os.path.join(here, "fixtures/vcr_cassettes")

USE_VCR = False


@pytest.hookimpl(hookwrapper=True)
def pytest_pyfunc_call(pyfuncitem):
    """Sorts through each test, uses a vcr cassette to run the test, storing the
    request results into a single file location"""
    cassette_name = hash_test_function(pyfuncitem)

    markers = pyfuncitem.own_markers

    record_modes = []
    for marker in markers:
        record_modes += marker.args

    if "no" not in record_modes and USE_VCR:
        myvcr.record_mode = record_modes[0]
        with myvcr.use_cassette(os.path.join(fixtures_path, cassette_name) + ".yaml"):
            outcome = yield  # runs the test
    else:
        outcome = yield  # runs the test


def pytest_collection_modifyitems(items):
    """Adds the 'webtest' marker to tests. Necessary to access a live server."""
    for item in items:
        item.add_marker("webtest")


###########
# Fixtures
###########

DEFAULTCONFIG = {
    "login": "neptune",
    "password": "aquarium",
    "aquarium_url": "http://0.0.0.0:80"
}


@pytest.fixture(scope="session")
def config():
    """
    Returns the config dictionary for live tests.
    """
    dir = os.path.dirname(os.path.abspath(__file__))

    config_path = os.path.join(dir, "secrets", "config.json.secret")
    if os.path.isfile(config_path):
        with open(config_path, "rU") as f:
            config = json.load(f)
        return config
    else:
        raise FileNotFoundError("No session login credentials found at {}. Please add file"
                                " to complete live tests.".format(config_path))


@pytest.fixture(scope="session")
def session(config):
    """
    Returns a live aquarium connection.
    """
    return AqSession(**config)
