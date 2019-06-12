from pydent.base import ModelRegistry
from pydent.models import __all__ as allmodels


def test_all_models():
    """
    Ensure __all__ contains all models registered by the ModelRegistry
    """
    missing_models = set(allmodels) - set(list(ModelRegistry.models.keys()))

    msg = "Missing models in pydent.models.__all__: {}"
    assert len(missing_models) == 0, msg.format(", ".join(missing_models))
