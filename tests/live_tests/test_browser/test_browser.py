import re

import pytest
from pydent import models
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
        assert isinstance(op_type, models.OperationType)


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
