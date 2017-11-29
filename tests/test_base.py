"""Tests for pydent.base.py"""

import pytest
from pydent import ModelBase, ModelRegistry
from pydent.exceptions import TridentModelNotFoundError
from pydent import AqSession
import copy

def test_model_base():


    m = ModelBase()
    assert m.session is None

def test_connect_to_session(fake_session):
    """Upon instantiation, modelbases should have no session. Connect to
    session should connect to a new session. Connecting to other sessions
    afterward should not be allowed."""
    m = ModelBase()
    assert m.session is None

    # connect to session
    m.connect_to_session(fake_session)
    assert m.session == fake_session

    # attempt to connect to another session
    fake_session2 = copy.copy(fake_session)
    m.connect_to_session(fake_session2)
    assert not m.session == fake_session2
    assert m.session == fake_session


def test_empty_relationships():

    m = ModelBase()
    assert m.get_relationships() == {}
    assert m.relationships == {}


def test_check_for_session(fake_session):
    """If session is none, _check_for_session should raise an AttributeError"""
    m = ModelBase()
    with pytest.raises(AttributeError):
        m._check_for_session()

    m.connect_to_session(fake_session)
    m._check_for_session()


def test_model_registry():
    """We expect get_model to return the value in the models dictionary"""
    class MyModel(ModelBase):
        pass

    assert "MyModel" in ModelRegistry.models
    assert ModelRegistry.models["MyModel"] == MyModel
    assert ModelRegistry.get_model("MyModel") == MyModel
    del ModelRegistry.models["MyModel"]


def test_no_model_in_registry():
    """ModelRegistry should raise error if model doesn't exist"""
    with pytest.raises(TridentModelNotFoundError):
        ModelRegistry.get_model("SomeModelThatDoesntExist")


def test_find_no_session():
    m = ModelBase()
    with pytest.raises(AttributeError):
        m.find_using_session(None, None)


def test_where_no_session():
    m = ModelBase()
    with pytest.raises(AttributeError):
        m.where_using_session(None, None)


def test_where_and_find(monkeypatch, fake_session):
    """Calling the 'where' wrapper on a ModelBase should attempt to
    get a model interface and call 'where' or 'find' on the interface.
    In this case, a fake model interface is returned in which the methods
    return the parameter passed in"""

    def fake_model_interface(self, model_name):
        """A fake model interface to test where"""
        class FakeInterface:
            def find(id):
                return id

            def where(params):
                return params
        return FakeInterface
    monkeypatch.setattr(AqSession, AqSession.model_interface.__name__, fake_model_interface)

    m = ModelBase()
    ModelRegistry.models["FakeModel"] = ModelBase
    m.connect_to_session(fake_session)
    assert m.where_using_session("FakeModel", 5) == 5
    assert m.find_using_session("FakeModel", 6) == 6


def test_print():
    m = ModelBase()
    print(m)
    m.print()
