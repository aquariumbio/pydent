import random
from uuid import uuid4

import pytest


@pytest.mark.record_mode("no")
@pytest.mark.parametrize("method", ["update", "save"])
def test_update_sample_description(session, method):
    """We expect the description to be updated on the server with 'update'."""
    s1 = session.Sample.one()
    x = str(uuid4())
    s1.description = x

    # save/update sample
    getattr(s1, method)()

    # get sample from server
    s2 = session.Sample.find(s1.id)

    assert s1.description == x, "Local sample description should be updated."
    assert s2.description == x, "Server and local description should match."


@pytest.mark.record_mode("no")
@pytest.mark.parametrize("method", ["update", "save"])
def test_refresh_sample_description(session, method):
    """We expect the description to be updated on the server with 'update'."""
    s1 = session.Sample.one()
    s2 = session.Sample.find(s1.id)
    x = str(uuid4())
    s1.description = x

    # save/update sample
    getattr(s1, method)()

    # refresh sample from server
    s2.refresh()

    assert s1.description == x, "Local sample description should be updated."
    assert s2.description == x, "Server and local description should match."


@pytest.mark.record_mode("no")
@pytest.mark.parametrize("method", ["update", "save"])
def test_update_sample_field_values(session, method):

    fragment_type = session.SampleType.find_by_name("Fragment")
    s1 = session.Sample.one(query={"sample_type_id": fragment_type.id})

    length = random.randint(0, 1000)
    s1.update_properties({"Length": length})

    assert s1.properties["Length"] == length

    getattr(s1, method)()

    s2 = session.Sample.find(s1.id)
    assert s2.properties["Length"] == length


@pytest.mark.record_mode("no")
@pytest.mark.parametrize("method", ["update", "save"])
def test_refresh_sample_field_values(session, method):

    fragment_type = session.SampleType.find_by_name("Fragment")
    s1 = session.Sample.one(query={"sample_type_id": fragment_type.id})
    s2 = session.Sample.find(s1.id)

    length = random.randint(0, 1000)
    s1.update_properties({"Length": length})

    assert s1.properties["Length"] == length

    getattr(s1, method)()

    s2.field_values = None
    s2.refresh()
    assert s2.properties["Length"] == length
