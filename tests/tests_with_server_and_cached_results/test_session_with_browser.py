from pydent.browser.browser_interface import BrowserInterface
from pydent.browser import Browser, BrowserSession
from copy import deepcopy


def test_regular_session(session):
    s1 = session.Sample.find(4)
    st1 = s1.sample_type
    s2 = session.Sample.find(4)
    st2 = session.SampleType.find(s1.sample_type_id)
    assert id(s1) != id(s2)
    assert id(st1) != id(st2)


def test_session_with_browser(session):
    session = deepcopy(session)
    session.INTERFACE_CLASS = BrowserInterface
    session.browser = Browser(session)
    session.initialize_interface()

    s1 = session.Sample.find(4)
    st1 = s1.sample_type
    s2 = session.Sample.find(4)
    st2 = session.SampleType.find(s1.sample_type_id)
    assert id(s1) == id(s2)
    assert id(st1) == id(st2)


def test_BrowserSession_from_session(session):
    bsession = BrowserSession.from_session(session)

    s1 = bsession.Sample.find(4)
    st1 = s1.sample_type
    s2 = bsession.Sample.find(4)
    st2 = bsession.SampleType.find(s1.sample_type_id)
    assert id(s1) == id(s2)
    assert id(st1) == id(st2)




