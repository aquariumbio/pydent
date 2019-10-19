import pytest

from pydent.browser import Browser


def test_first_last(session):
    browser = Browser(session)
    models = browser.first()
    assert len(models) == 1

    m1 = models[0]
    m2 = session.Sample.first()[0]
    m3 = session.Sample.last()[0]
    assert m1.id == m2.id
    assert m3.id != m2.id


def test_last(session):
    browser = Browser(session)
    models = browser.last()
    assert len(models) == 1

    m1 = models[0]
    m2 = session.Sample.last()[0]
    m3 = session.Sample.first()[0]
    assert m1.id == m2.id
    assert m3.id != m2.id


def test_one(session):
    browser = Browser(session)
    m1 = browser.one()
    m2 = session.Sample.one()
    m3 = session.Sample.last()[0]
    assert m1.id == m2.id
    assert m3.id == m2.id


@pytest.mark.parametrize("num", [1, 5, 10])
def test_last_with_num(session, num):
    browser = Browser(session)
    models = browser.last(num)
    assert len(models) == num


@pytest.mark.parametrize("num", [1, 5, 10])
def test_first_with_num(session, num):
    browser = Browser(session)
    models = browser.first(num)
    assert len(models) == num


@pytest.mark.parametrize("fname", ["first", "last"])
def test_query_with_query_returns_empty(session, fname):
    browser = Browser(session)
    fxn = getattr(browser, fname)
    models = fxn(query={"name": "Yokle"})
    assert models == []


@pytest.mark.parametrize("fname", ["first", "last"])
@pytest.mark.parametrize("stid", [1, 2, 5])
def test_query_with_sample_type(session, fname, stid):
    browser = Browser(session)
    st = session.SampleType.find(stid)
    fxn = getattr(browser, fname)
    models = fxn(sample_type=st.name)
    for m in models:
        assert m.sample_type_id == stid
