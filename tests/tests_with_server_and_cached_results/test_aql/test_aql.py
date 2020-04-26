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
examples_folder = join(here, "examples")
for filepath in glob(join(examples_folder, "*.json")):
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


@example_fixture
@pytest.mark.parametrize(
    "json_param",
    [
        False,
        True,
        {"include_uri": False},
        {"include_model_type": False},
        {"include_uri": False, "include_model_type": False},
        {"include_uri": False, "include_model_type": True},
        {"include_uri": True, "include_model_type": False},
        {"include_uri": True, "include_model_type": True},
    ],
)
def test_query_from_session_as_json(session, data, json_param):
    data["__json__"] = json_param
    results = session().query(data)
    assert isinstance(results, list)
    print(results)
    if results:
        assert isinstance(results[0], dict)
        if isinstance(json_param, dict):
            if "include_uri" in json_param:
                assert json_param["include_uri"] == ("__uri__" in results[0])
            if "include_model_type" in json_param:
                assert json_param["include_model_type"] == ("__model__" in results[0])
