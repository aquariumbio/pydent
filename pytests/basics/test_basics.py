import pytest

from pydent.models import SampleType, User, Sample, Item
from pydent.exceptions import TridentModelNotFoundError


# TODO: These tests are highly dependent on nursery server state


def test_raise_model_not_found_error(session):
    with pytest.raises(TridentModelNotFoundError):
        session.UUU.find(1)


def test_find_user(session):
    u = session.User.find(1)
    assert isinstance(u, User)
    assert len(u.name) > 1
    print(u.raw)
    print("User " + str(u.id) + " is named " + u.name)


def test_find_item(session):
    i = session.Item.find(1111)
    assert isinstance(i, Item)

def test_model_chaining(session):
    i = session.Item.find(1111)

    s = i.sample
    i.sample.sample_type.name
    i.sample.name
    i.created_at


def test_sample_type_all(session):
    sample_types = session.SampleType.all()
    assert len(sample_types) > 1
    assert isinstance(sample_types[0], SampleType)

def test_sample_find_by_name(session):
    s = session.Sample.find_by_name("pGFP")
    assert s.name == "pGFP"
    assert isinstance(s, Sample)


def test_sample_where(session):
    session.Sample.where({"id": [1231, 2341, 3451]})