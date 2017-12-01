from pydent.base import ModelRegistry
import warnings
from pydent.models import __all__ as allmodels


def test_all_models():
    """Ensure __all__ contains all models registered by the ModelRegistry"""
    missing_models = set(allmodels) - set(list(ModelRegistry.models.keys()))

    if len(missing_models) > 0:
        warnings.warn("Missing models in pydent.models.__all__: {}".format(', '.join(missing_models)))
