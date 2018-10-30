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

@pytest.fixture(scope="function")
def fake_sample(fake_session):
    sample_data = {
        'project': 'LightSwitch',
        'data': None,
        'id': 19763,
        'created_at': '2018-10-25T11:35:26.000-07:00',
        'name': 'pSNR52_sgpCUP1-8_tracrRNA_2xCOM_tSUP4-TP',
        'description': 'An a sgRNA cassette that recognizes sgpCUP1-8 and has the 2xCOM amptamer.',
        'user_id': 192,
        'updated_at': '2018-10-25T11:35:26.000-07:00',
        'sample_type_id': 4,
        'sample_type': {
            'id': 4,
            'created_at': '2013-10-16T14:33:41.000-07:00',
            'name': 'Fragment',
            'description': 'A linear double stranded piece of DNA from PCR or Restriction Digest',
            'updated_at': '2015-11-29T07:55:20.000-08:00',
            'field_types': [
                {
                    'part': None,
                    'id': 11,
                    'choices': None,
                    'name': 'Sequence',
                    'created_at': '2016-05-09T20:40:31.000-07:00',
                    'preferred_field_type_id': None,
                    'role': None,
                    'parent_class': 'SampleType',
                    'array': False,
                    'parent_id': 4,
                    'preferred_operation_type_id': None,
                    'updated_at': '2016-05-09T21:17:39.000-07:00',
                    'ftype': 'url',
                    'routing': None,
                    'required': True,
                    'rid': 76
                },
                {
                    'part': None,
                    'id': 12,
                    'choices': None,
                    'name': 'Length',
                    'created_at': '2016-05-09T20:40:31.000-07:00',
                    'preferred_field_type_id': None,
                    'role': None,
                    'parent_class': 'SampleType',
                    'array': False,
                    'parent_id': 4,
                    'preferred_operation_type_id': None,
                    'updated_at': '2016-05-09T21:17:39.000-07:00',
                    'ftype': 'number',
                    'routing': None,
                    'required': True,
                    'rid': 77
                },
                {
                    'part': None,
                    'id': 13,
                    'choices': None,
                    'name': 'Template',
                    'created_at': '2016-05-09T20:40:31.000-07:00',
                    'preferred_field_type_id': None,
                    'role': None,
                    'parent_class': 'SampleType',
                    'array': False,
                    'parent_id': 4,
                    'preferred_operation_type_id': None,
                    'updated_at': '2016-05-12T19:07:59.000-07:00',
                    'ftype': 'sample',
                    'routing': None,
                    'required': False,
                    'rid': 78
                },
                {
                    'part': None,
                    'id': 14,
                    'choices': None,
                    'name': 'Forward Primer',
                    'created_at': '2016-05-09T20:40:31.000-07:00',
                    'preferred_field_type_id': None,
                    'role': None,
                    'parent_class': 'SampleType',
                    'array': False,
                    'parent_id': 4,
                    'preferred_operation_type_id': None,
                    'updated_at': '2016-05-12T19:07:59.000-07:00',
                    'ftype': 'sample',
                    'routing': None,
                    'required': False,
                    'rid': 79
                },
                {
                    'part': None,
                    'id': 15,
                    'choices': None,
                    'name': 'Reverse Primer',
                    'created_at': '2016-05-09T20:40:31.000-07:00',
                    'preferred_field_type_id': None,
                    'role': None,
                    'parent_class': 'SampleType',
                    'array': False,
                    'parent_id': 4,
                    'preferred_operation_type_id': None,
                    'updated_at': '2016-05-12T19:07:59.000-07:00',
                    'ftype': 'sample',
                    'routing': None,
                    'required': False,
                    'rid': 80
                },
                {
                    'part': None,
                    'id': 16,
                    'choices': None,
                    'name': 'Restriction Enzyme(s)',
                    'created_at': '2016-05-09T20:40:31.000-07:00',
                    'preferred_field_type_id': None,
                    'role': None,
                    'parent_class': 'SampleType',
                    'array': False,
                    'parent_id': 4,
                    'preferred_operation_type_id': None,
                    'updated_at': '2016-05-09T21:17:39.000-07:00',
                    'ftype': 'string',
                    'routing': None,
                    'required': False,
                    'rid': 81
                },
                {
                    'part': None,
                    'id': 17,
                    'choices': None,
                    'name': 'Yeast Marker',
                    'created_at': '2016-05-09T20:40:31.000-07:00',
                    'preferred_field_type_id': None,
                    'role': None,
                    'parent_class': 'SampleType',
                    'array': False,
                    'parent_id': 4,
                    'preferred_operation_type_id': None,
                    'updated_at': '2016-05-09T21:17:39.000-07:00',
                    'ftype': 'string',
                    'routing': None,
                    'required': False,
                    'rid': 82
                },
                {
                    'part': None,
                    'id': 16032,
                    'choices': None,
                    'name': 'Fragment Mix Array',
                    'created_at': '2018-10-23T13:31:46.000-07:00',
                    'preferred_field_type_id': None,
                    'role': None,
                    'parent_class': 'SampleType',
                    'array': True,
                    'parent_id': 4,
                    'preferred_operation_type_id': None,
                    'updated_at': '2018-10-23T20:25:42.000-07:00',
                    'ftype': 'sample',
                    'routing': None,
                    'required': False,
                    'rid': 83
                }
            ],
            'rid': 47
        },
        'rid': 45
    }
    return fake_session.Sample.load(sample_data)


@pytest.mark.parametrize("num_field_values", list(range(1)))
def test_update_properties_of_field_value_array(fake_sample, num_field_values):
    fake_sample.set_field_value_array('Fragment Mix Array', [fake_sample]*num_field_values)
