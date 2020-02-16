import json
from glob import glob
from os.path import abspath
from os.path import dirname
from os.path import join

import pytest

from pydent.aql import aql
from pydent.aql import validate_aql

here = abspath(dirname(__file__))


def load(filepath):
    with open(filepath, "r") as f:
        return json.load(f)


examples = []
for filepath in glob(join(here, "examples", "*.json")):
    examples.append(load(filepath))
example_ids = [e["__description__"] for e in examples]

example_fixture = pytest.mark.parametrize("data", examples, ids=example_ids)


@example_fixture
def test_validate(data):
    validate_aql(data)


@example_fixture
def test_aquarium_query_language_method(session, data):
    with session.with_cache() as sess:
        aql(sess, data)


@example_fixture
def test_query_from_session(session, data):
    session().query(data)
