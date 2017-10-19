import pytest
from pydent import *

def assert_eq(m1, m2):
    assert m1.__dict__ == m2.__dict__

def test_model(load_session):
    model = SampleType
    all = model.all()
    for i in [0, -1]:
        m = all[i]
        print(m.__dict__)
        m2 = model.find_by_name(m.name)
        assert m == m2
        # assert model.find(m.id) == m
        # assert model.where({"id": m.id}) == [m]
        # attributes accessible?