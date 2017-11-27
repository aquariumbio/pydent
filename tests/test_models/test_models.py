from pydent.models import __all__ as allmodels
from pydent.base import ModelRegistry
import warnings


def test_all_models():
    """Ensure __all__ contains all models registered by the ModelRegistry"""
    assert allmodels == list(ModelRegistry.models.keys())
    missing_models = set(allmodels) - set(list(ModelRegistry.models.keys()))

    if len(missing_models) > 0:
        warnings.warn("Missing models in pydent.models.__all__: {}".format(', '.join(missing_models)))


def test_field_value(session):
    primer = session.Sample.find(1)
    primer_type = primer.sample_type

    fvs = primer.field_values
    fv = fvs[0]
    print(fvs.name)

    fv_data = fv.dump(dump_all_relations=True)

    from pydent.models import FieldValue

    fv2 = FieldValue.load(fv_data)
    print(fv2.dump())

