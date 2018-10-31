import pytest

import json
import os

here = os.path.abspath(os.path.dirname(__file__))


@pytest.fixture(scope="function")
def example_plan(fake_session):
    with open(os.path.join(here, 'plan_example.json'), 'r') as f:
        plan_data = json.load(f)
    return fake_session.Plan.load(plan_data)