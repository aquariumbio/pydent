import pytest
from pydent import AqSession
from pydent.models import *
from marshmallow import pprint
import uuid
@pytest.fixture(scope='function')
def local_session():
    return AqSession("guest", "password", "http://0.0.0.0:3000")

def test_sample(local_session):
    sample = local_session.Sample.find(1)
    fts = sample.sample_type.field_types
    print(fts)

    fv = sample.field_values[0]

    assert fv.operation is None
    assert isinstance(fv.parent_sample, Sample)
    print(fv)
    print(fv.allowable_field_type)

def test_create_sample(local_session):

    new_sample = Sample(name=str(uuid.uuid4()), project="MyProject", sample_type_id=1)
    print(new_sample.dump())
    s = local_session.utils.create_samples([new_sample])
    print(s)