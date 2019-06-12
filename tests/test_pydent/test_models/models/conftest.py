import pytest

import json
import os

here = os.path.abspath(os.path.dirname(__file__))


@pytest.fixture(scope="function")
def example_plan(fake_session):
    with open(os.path.join(here, "plan_example.json"), "r") as f:
        plan_data = json.load(f)
    return fake_session.Plan.load(plan_data)


@pytest.fixture(scope="function")
def example_sample(fake_session):
    with open(os.path.join(here, "sample_example.json"), "r") as f:
        data = json.load(f)
    sample = fake_session.Sample.load(data)
    return sample
