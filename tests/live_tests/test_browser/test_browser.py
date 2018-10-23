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


def test_cache_where(session):
    browser = Browser(session)
    primers = browser.cached_where("Sample", {"sample_type_id": 1})

    p = primers[-1]
    p.__dict__['foo'] = 'bar'

    cached_primers = browser.cached_where("Sample", {"sample_type_id": 1, "id": p.id})
    cached_primers2 = browser.cached_where("Sample", {"sample_type_id": [1,2], "id": [p.id]})
    empty = browser.cached_where("Sample", {"sample_type_id": 2, "id": p.id})

    assert empty == [], 'should not return any primers since query does not match'
    assert len(cached_primers) == 1, 'should return exactly 1 primer'
    assert cached_primers2 == cached_primers, 'should be equivalent as these are equivalent queries'
    assert 'foo' in cached_primers[0].__dict__, 'should containg the "foo" attribute that was initially cached'
    assert cached_primers[0].__dict__['foo'] == 'bar', 'should return the very same models that was initially cached'
    assert len(browser.model_cache['Sample']) > 1


def test_cache_find(session):
    browser = Browser(session)
    primers = browser.cached_where("Sample", {"sample_type_id": 1})

    p = primers[-1]
    p.__dict__['foo'] = 'bar'

    cached_primer = browser.cached_find("Sample", p.id)
    cached_primers = browser.cached_find("Sample", [p.id])
    empty = browser.cached_find("Sample", 100000)

    assert empty is None, 'should not return any primers since query does not match'
    assert cached_primer == p
    assert len(cached_primers) == 1
    assert cached_primer == cached_primers[0]


def test_recursive_cache(session):

    browser = Browser(session)
    samples = browser.interface('Sample').where({'sample_type_id': 1})

    # should preload SampleType into cache
    st = browser.find(1, 'SampleType')
    assert browser.model_cache['SampleType'][st.id] == st

    # should retrieve the exact model that was preloaded
    browser.retrieve(samples, 'sample_type')
    assert samples[0].sample_type is st

    # affecting sample_types from these models should refer to the same sample type
    assert samples[0].sample_type is samples[1].sample_type


def test_recursive_cache_plan(session):

    browser = Browser(session)

    ops = session.Operation.last(50)
    browser.set_verbose(True)
    browser.recursive_retrieve(ops, {
        "operation_type": {
            "field_types": {
                "allowable_field_types": "field_type"
            }
        },
        "field_values": "field_type"
    })

    op = ops[-10]

    ft = op.operation_type.field_types[0]
    fv = op.field_value(ft.name, ft.role)

    assert ft.rid is fv.field_type.rid

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

    filtered_primers = browser.filter_by_properties(primers, {"T Anneal": 64})

    assert len(filtered_primers) > 0
    assert len(primers) > len(filtered_primers)
    for primer in filtered_primers:
        assert primer.properties["T Anneal"] == '64'


def test_filter_by_sample_properties_with_inequality(session):
    browser = Browser(session)
    primers = browser.search(".*gfp.*", sample_type="Primer")

    filtered_primers = browser.filter_by_properties(primers, "value > 64")

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


def test_retrieve_query_with_field_values(session):
    """The retrieve helper method should use the relationship definition
    of the callback_args to query FieldValues based on their parent_id
    AND parent_class."""
    browser = Browser(session)
    sample = session.Sample.one()
    relation = sample.relationships['field_values']
    query = browser._collect_callback_args([sample], relation)
    assert query == {
        'parent_class': ['Sample'],
        'parent_id': [sample.id]
    }


def test_retrieve_with_many_field_values(session):
    browser = Browser(session)
    samples = browser.search(".*mcherry.*", sample_type='Fragment')[:30]
    assert len(samples[0].field_values) > 0
    assert 'items' not in samples[0].__dict__, "Items should not have been loaded into the sample yet."
    field_values = browser._retrieve_has_many_or_has_one(samples, 'field_values')
    assert len(field_values) > 0


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
        assert 'operations' not in j.__dict__

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


def test_retrieve_fidelity(session):
    """Retrieve should never change the model definition"""

    items = session.Sample.last(10)
    fvs = []
    for i in items:
        for _fv in i.field_values:
            fvs.append(_fv.id)

    fvs2 = []
    browser = Browser(session)
    browser.retrieve(items, 'field_values')
    for i in items:
        for _fv in i.field_values:
            fvs2.append(_fv.id)

    assert fvs == fvs2


# TODO: do we want retrieve to force a new query?, if its new, it is just ignored for now...
def test_retrieve_with_new_operations(session):
    """We expect when we create new models for the model relationships to be maintained"""

    ots = [session.OperationType.find_by_name(x) for x in ["Make PCR Fragment", "Check Plate", "Make Miniprep"]]
    ops = [ot.instance() for ot in ots]

    ots_arr1 = []
    for op in ops:
        ots_arr1.append(op.operation_type.id)

    browser = Browser(session)
    browser.retrieve(ops, 'operation_type')

    ots_arr2 = []
    for op in ops:
        ots_arr2.append(op.operation_type.id)

    assert ots_arr1 == ots_arr2

def test_retrieve_with_new_samples(session):
    """We expect when we create new models for the model relationships to be maintained"""

    samp1 = session.SampleType.find_by_name("Primer").new_sample(
        '', '', '', properties={
            "Anneal Sequence": "AGTAGTATGA"
        }
    )
    samp2 = session.SampleType.find_by_name("Fragment").new_sample(
        '', '', '', properties={
            "Length": 100,
            "Forward Primer": samp1
        }
    )

    fvs = []
    samples = [samp1, samp2]
    for s in samples:
        fvs += s.field_values

    browser = Browser(session)
    browser.retrieve(samples, 'field_values')

    fvs2 = []
    samples = [samp1, samp2]
    for s in samples:
        fvs2 += s.field_values

    assert fvs == fvs2



