from pydent import models


def test_find_returns_none(session):
    """Find queries should return None, if model is not found"""
    x = session.Operation.find(1000000000000)
    assert x is None


def test_where_returns_empty_array(session):
    """Where queries should return an empty array if no models are found (not None)"""
    x = session.Operation.where({"id": 20947983476893498573987})
    assert x == []


def test_first_default_params(session):
    x = session.SampleType.first()
    assert len(x) == 1
    assert x[0].id == 1


def test_first_with_5(session):
    x = session.SampleType.first(5)
    assert len(x) == 5


def test_last_default_params(session):
    x = session.SampleType.last()
    assert len(x) == 1
    assert x[0].id > 1


def test_first_and_last_with_default(session):
    first_models = session.SampleType.first()
    last_models = session.SampleType.last()
    assert len(first_models) == 1, "first() should return exactly one model in a list"
    assert len(last_models) == 1, "last() should return exactly one model in a list"
    assert first_models[0].id < last_models[0].id, "The first model id should have a smaller id than the last model"
    assert isinstance(first_models[0], models.SampleType), "The first model should be a SampleType"
    assert isinstance(last_models[0], models.SampleType), "The last model should be a SampleType"


def test_first_and_last_with_num(session):
    first_models = session.SampleType.first(5)
    last_models = session.SampleType.first(6)

    assert len(first_models) == 5
    assert len(last_models) == 6

    for f in first_models:
        assert isinstance(f, models.SampleType), "The last model should be a SampleType"

    for l in last_models:
        assert isinstance(l, models.SampleType), "The last model should be a SampleType"


def test_first_and_last_with_query(session):
    first_samples = session.Sample.first(2, sample_type_id=1)
    last_samples = session.Sample.last(3, sample_type_id=1)

    for f in first_samples:
        assert f.sample_type_id == 1
    for l in last_samples:
        assert l.sample_type_id == 1


def test_first_and_last_with_diff_models(session):
    first_sample_types = session.SampleType.first()
    first_samples = session.Sample.first()
    last_sample_types = session.SampleType.last()
    last_samples = session.Sample.last()

    assert isinstance(first_sample_types[0], models.SampleType), "The first model should be a SampleType"
    assert isinstance(last_sample_types[0], models.SampleType), "The last model should be a SampleType"
    assert isinstance(first_samples[0], models.Sample), "The first model should be a SampleType"
    assert isinstance(last_samples[0], models.Sample), "The last model should be a SampleType"


def test_one_default(session):
    first = session.SampleType.one(first=True)
    last = session.SampleType.one()
    assert first.id < last.id, "The first model id should have a smaller id than the last model"
    assert isinstance(first, models.SampleType), "The first model should be a SampleType"
    assert isinstance(last, models.SampleType), "The last model should be a SampleType"


def test_one_with_query(session):

    last = session.Sample.one(sample_type_id=1)
    assert last.sample_type_id == 1, "Sample should have a sample_type_id of 1"


def test_one_returns_none(session):
    last = session.Sample.one(nonexistant=1)
    assert last is None, "should be None"


def test_first_and_last_returns_emtpy(session):
    last = session.Sample.first(5, nonexistant=1)
    first = session.Sample.first(5, nonexistant=1)
    assert last == [], "should be empty"
    assert first == [], "should be empty"
