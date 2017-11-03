import pytest
from pydent.aq import SampleType, User, Sample, Item


def test_find_user():
    u = User.find(1)
    assert len(u.name) > 1
    print("User " + str(u.id) + " is named " + u.name)


def test_find_item():
    i = Item.find(1111)
    i.sample.sample_type.name
    i.sample.name
    i.created_at


def test_sample_type_all():
    assert len(SampleType.all()) > 1


def test_sample_find_by_name():
    Sample.find_by_name("pGFP")


def test_sample_where():
    Sample.where({"id": [1231, 2341, 3451]})


def test_sample_type_all():
    l = SampleType.all()
    assert len(l) > 0
