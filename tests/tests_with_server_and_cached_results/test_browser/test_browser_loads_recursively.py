import pytest

from pydent.browser import Browser


@pytest.mark.skip("This is no possible in Aquarium 2.7")
def test_browser_loads_wires(session):
    """The Plan class has a special query hook that automatically grabs wires
    as well.

    By default, the update cache will recursively update models that
    have been deserialized from a model list. We expect that the 'Wire'
    model is in the model cache when we load a plan.
    """

    browser = Browser(session)
    assert "Wire" not in browser.model_cache
    browser.one("Plan")
    assert "Wire" in browser.model_cache
