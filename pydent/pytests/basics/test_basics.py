import pytest
from pydent import *

def test_sample_type_all(load_session):
    g = globals()
    s = SampleType
    SampleType.all()

def test_find_user(load_session):
    u = aq.User.find(1)
    assert len(u.name) > 1
    print("User " + str(u.id) + " is named " + u.name)

def test_find_item(load_session):
    i = aq.Item.find(1111)
    i.sample.sample_type.name
    i.sample.name
    i.created_at

def test_sample_type_all(load_session):
    assert len(aq.SampleType.all()) > 1

def test_sample_find_by_name(load_session):
    aq.Sample.find_by_name("pGFP")

def test_sample_where(load_session):
    aq.Sample.where({"id": [1231, 2341, 3451]})