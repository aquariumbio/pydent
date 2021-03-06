import pytest

from pydent.base import ModelRegistry
from pydent.marshaller.exceptions import ModelRegistryError


def test_did_you_mean():
    """ModelRegistry should suggest the closest model names in the error
    message."""
    with pytest.raises(ModelRegistryError) as e:
        ModelRegistry.get_model("SampleTypes")
    print(str(e.value))
    assert "Did you mean" in str(e.value)
    assert "SampleType" in str(e.value)

    with pytest.raises(ModelRegistryError) as e:
        ModelRegistry.get_model("collection")
    print(str(e.value))
    assert "Did you mean" in str(e.value)
    assert "Collection" in str(e.value)
    assert "SampleType" not in str(e.value)

    with pytest.raises(ModelRegistryError) as e:
        ModelRegistry.get_model("asdfasdrfasd")
    print(str(e.value))


def test_did_you_mean_for_session(fake_session):

    with pytest.raises(AttributeError) as e:
        fake_session.find
    assert "Did you mean" in str(e.value)


def test_did_you_mean_for_model_session(fake_session):

    with pytest.raises(AttributeError) as e:
        fake_session.Samples
    assert "Did you mean" in str(e.value)
