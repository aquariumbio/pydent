"""Tests for the new session cache. The cache is initalizes in sessions using a
browser or sessions with.

.. versionadded:: 0.1
"""
from abc import ABC
from copy import deepcopy

import pytest

from pydent.exceptions import ForbiddenRequestError
from pydent.interfaces import BrowserInterface


def test_regular_session(session):
    s1 = session.Sample.find(4)
    st1 = s1.sample_type
    s2 = session.Sample.find(4)
    st2 = session.SampleType.find(s1.sample_type_id)
    assert id(s1) != id(s2)
    assert id(st1) != id(st2)


def test_with_statement_moves_samples(session):

    with session.with_cache() as sess:
        m = sess.Sample.one()
        assert m.session is sess
        assert m.session is not session
    assert m.session is session


def test_swap_sessions(session):

    with session.with_cache() as s1:
        samples = s1.Sample.last(10)
        with s1(using_models=True, using_requests=False) as s2:
            for s in samples:
                assert s is s2.browser.model_cache["Sample"][s.id]
            for s in samples:
                assert s.session is s1
            s2._swap_sessions(s1, s2)
            for s in samples:
                assert s.session is s2

            with pytest.raises(ForbiddenRequestError):
                samples[0].sample_type


def test_raise_value_error_for_interface(session):
    class MyClass(ABC):
        pass

    with pytest.raises(ValueError):
        session.interface_class = MyClass


def test_session_with_browser(session):
    session = deepcopy(session)
    session.interface_class = BrowserInterface
    session.init_cache()
    session._initialize_interfaces()

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
    with session.with_cache() as sess:
        s1 = sess.Sample.one()
        st1 = s1.sample_type
        s2 = sess.Sample.one()
        st2 = sess.SampleType.find(s1.sample_type_id)
        assert id(st1) == id(st2)

        assert not s2.session is session
        assert s2.session is sess

    assert s2.session is session


def test_requests_off(session):

    with session.with_cache() as sess:
        s = sess.Sample.one()
        with sess.with_requests_off() as sess2:
            sess2.Sample.find(s.id)

            with pytest.raises(ForbiddenRequestError):
                sess2.Sample.one()

            with pytest.raises(ForbiddenRequestError):
                sess2.Sample.last(2)

    session.Sample.one()
