import os
import json
import pytest
from pydent.models import AquariumModelError
here = os.path.dirname(os.path.abspath(__file__))
dump_location = os.path.join(here, 'yeast_strain_dump.json')

## only run once...
# def test_dump(session):
#     data = session.SampleType.find_by_name("Yeast Strain").dump(include={
#         "field_types": {
#             "allowable_field_types":
#                 {
#                     "sample_type",
#                     "object_type"
#                 }
#         }
#     }
#     )
#     with open(dump_location, 'w') as f:
#         json.dump(data, f)

#
# def test_load(session):
#     with open(dump_location, 'r') as f:
#         yeast_strain = session.SampleType.load(json.load(f))
#
#     yeast = fake_session.Sample.new(
#         sample_type_id = yeast_strain.id,
#         sample_type=yeast_strain,
#         properties = {
#             'QC_length': 1000
#         }
#     )


def test_create_with_no_properties(session):

    yeast_strain = session.SampleType.find_by_name("Yeast Strain")
    yeast = session.Sample.new(
        sample_type_id=yeast_strain.id
    )



def test_create_with_integer_properties(session):

    yeast_strain = session.SampleType.find_by_name("Yeast Strain")
    yeast = session.Sample.new(
        sample_type_id=yeast_strain.id,
        properties={
            'QC_length': 100
        }
    )
    assert yeast.properties['QC_length'] == 100


def test_create_with_sample_properties(session):

    yeast_strain = session.SampleType.find_by_name("Yeast Strain")
    parent = yeast_strain.samples[-1]
    yeast = session.Sample.new(
        sample_type_id=yeast_strain.id,
        properties={
            'Parent': parent
        }
    )
    assert yeast.properties['Parent'] == parent


def test_create_with_sample_property_raises_exception(session):

    yeast_strain = session.SampleType.find_by_name("Yeast Strain")
    with pytest.raises(Exception):
        yeast = session.Sample.new(
            sample_type_id=yeast_strain.id,
            properties={
                'Parent': 1
            }
        )


# TODO: fix this text for raising when setting improper FieldValue for samples
# def test_create_with_integer_property_raises_exception(session):
#
#     yeast_strain = session.SampleType.find_by_name("Yeast Strain")
#     parent = yeast_strain.samples[-1]
#     with pytest.raises(Exception):
#         yeast = session.Sample.new(
#             sample_type_id=yeast_strain.id,
#             properties={
#                 'QC_length': parent
#             }
#         )


def test_create_raises_exception_when_property_is_not_found(session):

    yeast_strain = session.SampleType.find_by_name("Yeast Strain")
    with pytest.raises(Exception):
        yeast = session.Sample.new(
            sample_type_id=yeast_strain.id,
            properties={
                'Not a field value name': 1
            }
        )

def test_create_raises_exception_with_wrong_choice(session):
    yeast_strain = session.SampleType.find_by_name("Yeast Strain")
    with pytest.raises(AquariumModelError):
        yeast = session.Sample.new(
            sample_type_id=yeast_strain.id,
            properties={
                'Mating Type': "not a mating type"
            }
        )


def test_create_with_choice(session):
    yeast_strain = session.SampleType.find_by_name("Yeast Strain")
    yeast = session.Sample.new(
            sample_type_id=yeast_strain.id,
            properties={
                'Mating Type': "MATa"
            }
        )
    assert yeast.properties["Mating Type"] == "MATa"


def test_update_properties(session):

    yeast_strain = session.SampleType.find_by_name("Yeast Strain")
    yeast = session.Sample.new(sample_type_id=yeast_strain.id,
        properties={
            "QC_length": 200,
            "Comp_cell_limit": "Yes"
        }
    )
    parent = yeast_strain.samples[-1]
    yeast.update_properties({"Mating Type": "MATa", "Parent": parent, "QC_length": 100})

    assert yeast.properties["Mating Type"] == "MATa"
    assert yeast.properties["Parent"] == parent
    assert yeast.properties["QC_length"] == 100
