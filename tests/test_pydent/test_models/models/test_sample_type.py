import pytest

from pydent.models import SampleType

def test_sample_type_serialization(fake_session):
    sample_type = fake_session.SampleType(name='Fluff')
    object_type = fake_session.ObjectType(name='Big Tub')
    type = fake_session.AllowableFieldType(sample_type=sample_type, object_type=object_type)
    field_type = fake_session.FieldType(
        name='prop1',
        ftype='sample',
        allowable_field_types=[type]
    )
    sample_type = fake_session.SampleType(
        name="dummy",
        description="a dummy type",
        field_types=[field_type]
    )

    assert sample_type is not None
    # TODO: want to test that object is the same when retrieved
