import pytest

from pydent.marshaller import ModelRegistry


@pytest.mark.parametrize("modelname", ModelRegistry.models)
def test_all_models_have_one(session, modelname):
    session._aqhttp.log.set_level("DEBUG")
    inst = getattr(session, modelname).one()
    assert inst


@pytest.mark.parametrize("modelname", ModelRegistry.models)
def test_all_models_have_last(session, modelname):
    session._aqhttp.log.set_level("DEBUG")
    inst = getattr(session, modelname).last(1)
    assert len(inst) == 1


@pytest.mark.parametrize("modelname", ModelRegistry.models)
def test_all_models_have_first(session, modelname):
    session._aqhttp.log.set_level("DEBUG")
    inst = getattr(session, modelname).first(1)
    assert len(inst) == 1
