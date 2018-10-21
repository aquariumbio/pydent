import re

import pytest
from pydent import models as pydent_models
from pydent.browser import Browser
from pydent.exceptions import TridentModelNotFoundError


def test_search(session):
    browser = Browser(session)

    pattern = ".*GFP.*"
    samples = browser.search(pattern)

    assert len(samples) > 0
    for s in samples:
        assert re.match(pattern, s.name, re.IGNORECASE)


def test_search_ignore_case(session):
    browser = Browser(session)

    pattern = ".*mCherry.*"
    samples = browser.search(pattern, ignore_case=False)
    samples_without_case = browser.search(pattern, ignore_case=True)
    assert len(samples_without_case) > len(samples)
    assert len(samples) > 0
    for s in samples:
        assert re.match(pattern, s.name)


def test_search_with_sample_type(session):
    browser = Browser(session)

    pattern = ".*GFP.*"
    samples = browser.search(pattern, sample_type='Plasmid')

    assert len(samples) > 0
    sample_type = session.SampleType.find_by_name("Plasmid")

    for s in samples:
        assert s.sample_type_id == sample_type.id


def test_close_matches_with_sample_type(session):
    browser = Browser(session)

    pattern = "pMOD8-pGRR-W8"
    samples = browser.close_matches(pattern, sample_type="Plasmid")

    assert len(samples) > 0
    sample_type = session.SampleType.find_by_name("Plasmid")

    for s in samples:
        assert s.sample_type_id == sample_type.id


# TODO: Need a better test for close_matches
def test_close_match(session):
    browser = Browser(session)
    samples = browser.close_matches("pMOD8-pGRR-W8")
    assert len(samples) > 1


def test_cache(session):
    browser = Browser(session)
    browser.use_cache = True
    raise NotImplementedError("I don't know how to test this...")


def test_set_model_error(session):
    browser = Browser(session)

    with pytest.raises(TridentModelNotFoundError):
        browser.set_model("Op")


def test_set_model(session):
    browser = Browser(session)
    browser.set_model("OperationType")
    op_types = browser.search(".*Fragment.*")

    for op_type in op_types:
        assert isinstance(op_type, pydent_models.OperationType)


def test_filter_by_sample_properties(session):
    browser = Browser(session)
    primers = browser.search(".*gfp.*", sample_type="Primer")

    filtered_primers = browser.filter_by_field_value_properties(primers, {"T Anneal": 64})

    assert len(filtered_primers) > 0

    for primer in filtered_primers:
        assert primer.properties["T Anneal"] == '64'


def test_filter_by_sample_properties_with_inequality(session):
    browser = Browser(session)
    primers = browser.search(".*gfp.*", sample_type="Primer")

    filtered_primers = browser.filter_by_field_value_properties(primers, {"T Anneal": 'value > 64'})

    assert len(filtered_primers) > 0

    for primer in filtered_primers:
        assert int(primer.properties["T Anneal"]) > 64


def test_filter_operation_by_field_values(session):
    raise NotImplementedError()


def test_find_sample_by_properties(session):
    raise NotImplementedError


def test_save_sample_exists_strict(session):
    browser = Browser(session)
    raise NotImplementedError


def test_save_sample_exists_overwrite(session):
    browser = Browser(session)
    raise NotImplementedError


def test_save_sample_exists(session):
    browser = Browser(session)
    raise NotImplementedError


def test_update_sample(session):
    browser = Browser(session)
    raise NotImplementedError


def test_save_sample(session):
    browser = Browser(session)
    raise NotImplementedError


def test_update_model(session):
    browser = Browser(session)
    raise NotImplementedError


def test_retrieve_with_many(session):
    browser = Browser(session)
    samples = browser.search(".*mcherry.*", sample_type='Fragment')[:30]

    assert 'items' not in samples[0].__dict__, "Items should not have been loaded into the sample yet."
    browser._retrieve_has_many_or_has_one(samples, 'items')
    assert 'items' in samples[0].__dict__
    assert len(samples[0].__dict__['items']) > 0, "Items should have been found."


def test_retrieve_with_many_field_values(session):
    session.set_verbose(True)
    browser = Browser(session)
    samples = browser.search(".*mcherry.*", sample_type='Fragment')[:30]
    assert len(samples[0].field_values) > 0
    assert 'items' not in samples[0].__dict__, "Items should not have been loaded into the sample yet."
    browser._retrieve_has_many_or_has_one(samples, 'field_values')


def test_retrieve_with_one(session):
    browser = Browser(session)
    samples = browser.search(".*mcherry.*", sample_type='Fragment')[:30]
    assert 'sample_type' not in samples[0].__dict__, "SampleType should not have been loaded into the sample yet."
    sample_types = browser._retrieve_has_many_or_has_one(samples, 'sample_type')
    assert 'sample_type' in samples[0].__dict__, "SampleType should have been loaded"
    assert samples[0].__dict__['sample_type'].id, session.SampleType.find_by_name("Fragment").id
    assert isinstance(sample_types[0], pydent_models.SampleType)


def test_retrieve_with_many_through_for_jobs_and_operations(session):
    browser = Browser(session)
    jobs = session.Job.last(50)

    for j in jobs:
        assert not 'operations' in j.__dict__

    operations = browser._retrieve_has_many_through(jobs, 'operations')
    assert len(operations) > 0
    assert not all([m.__dict__['operations'] is None for m in jobs])

    for model in jobs:
        assert 'operations' in model.__dict__
        other_models = model.__dict__['operations']
        if other_models is not None:
            for other_model in other_models:
                assert isinstance(other_model, pydent_models.Operation)


def test_retrieve_with_many_through_for_collections_and_parts(session):
    browser = Browser(session)
    collections = session.Collection.last(50)

    for c in collections:
        assert not 'parts' in c.__dict__

    parts = browser._retrieve_has_many_through(collections, 'parts')
    assert len(parts) > 0
    assert not all([m.__dict__['parts'] is None for m in collections])

    for model in collections:
        assert 'parts' in model.__dict__
        other_models = model.__dict__['parts']
        if other_models is not None:
            for other_model in other_models:
                assert isinstance(other_model, pydent_models.Item)


def test_retrieve(session):
    """Should be able to parse HasOne, HasMany, and HasManyThrough without specifying the type of relationship."""
    browser = Browser(session)

    collections = session.Collection.last(50)
    parts = browser.retrieve(collections, 'parts')
    assert len(parts) > 0
    for model in collections:
        assert 'parts' in model.__dict__
        other_models = model.__dict__['parts']
        if other_models is not None:
            for other_model in other_models:
                assert isinstance(other_model, pydent_models.Item)

    jobs = session.Job.last(50)
    operations = browser._retrieve_has_many_through(jobs, 'operations')
    assert len(operations) > 0
    for model in jobs:
        assert 'operations' in model.__dict__
        other_models = model.__dict__['operations']
        if other_models is not None:
            for other_model in other_models:
                assert isinstance(other_model, pydent_models.Operation)

    samples = browser.search(".*mcherry.*", sample_type='Fragment')[:30]
    assert 'sample_type' not in samples[0].__dict__, "SampleType should not have been loaded into the sample yet."
    sample_types = browser._retrieve_has_many_or_has_one(samples, 'sample_type')
    assert len(sample_types) > 0
    assert samples[0].__dict__['sample_type'].id, session.SampleType.find_by_name("Fragment").id


def test_recursive_retrieve(session):

    browser = Browser(session)
    d = {
        "field_values": {
            "wires_as_dest": {
                "source": "operation",
                "destination": "operation"
            },
            "wires_as_source": {
                "source": "operation",
                "destination": "operation"
            },
        }
    }

    ops = browser.session.Operation.last(10)
    r = browser.recursive_retrieve(ops, d)

    assert len(r['field_values']) > 0
    assert len(r['wires_as_dest']) > 0
    assert len(r['wires_as_source']) > 0
    assert len(r['source']) > 0
    assert len(r['destination']) > 0
    assert len(r['operation']) > 0
    assert 'field_values' in ops[0].__dict__
    assert 'wires_as_dest' in ops[0].field_values[0].__dict__
    assert 'wires_as_source' in ops[0].field_values[0].__dict__
