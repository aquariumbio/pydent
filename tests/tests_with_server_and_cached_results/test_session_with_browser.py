from copy import deepcopy
import pytest
from pydent.interfaces import BrowserInterface
from abc import ABC
from pydent.exceptions import ForbiddenRequestError

def test_regular_session(session):
    s1 = session.Sample.find(4)
    st1 = s1.sample_type
    s2 = session.Sample.find(4)
    st2 = session.SampleType.find(s1.sample_type_id)
    assert id(s1) != id(s2)
    assert id(st1) != id(st2)


def test_raise_value_error_for_interface(session):
    class MyClass(ABC):
        pass
    with pytest.raises(ValueError):
        session.interface_class = MyClass


def test_session_with_browser(session):
    session = deepcopy(session)
    session.interface_class = BrowserInterface
    session.init_cache()
    session.initialize_interfaces()

    s1 = session.Sample.find(4)
    st1 = s1.sample_type
    s2 = session.Sample.find(4)
    st2 = session.SampleType.find(s1.sample_type_id)
    assert id(s1) == id(s2)
    assert id(st1) == id(st2)


def test_using_cache_with_session(session):
    session = deepcopy(session)
    session.using_cache = True
    s1 = session.Sample.find(4)
    st1 = s1.sample_type
    s2 = session.Sample.find(4)
    st2 = session.SampleType.find(s1.sample_type_id)
    assert id(s1) == id(s2)
    assert id(st1) == id(st2)


def test_cache_clear(session):
    bsession = session.copy()
    bsession.using_cache = True

    s1 = bsession.Sample.find(4)
    st1 = s1.sample_type

    bsession.clear_cache()

    s2 = bsession.Sample.find(4)
    st2 = bsession.SampleType.find(s1.sample_type_id)
    assert id(s1) != id(s2)
    assert id(st1) != id(st2)


def test_with_temp_cache(session):
    with session.temp_cache() as sess:
        s1 = sess.Sample.one()
        st1 = s1.sample_type
        s2 = sess.Sample.one()
        st2 = sess.SampleType.find(s1.sample_type_id)
        assert id(s1) == id(s2)
        assert id(st1) == id(st2)

        assert not s2.session is session
        assert s2.session is sess

    assert s2.session is session


def test_requests_off(session):

    with session.temp_cache() as sess:
        s = sess.Sample.one()
        with sess.requests_off() as sess2:
            sess2.Sample.find(s.id)

            with pytest.raises(ForbiddenRequestError):
                sess2.Sample.one()

            with pytest.raises(ForbiddenRequestError):
                sess2.Sample.last(2)