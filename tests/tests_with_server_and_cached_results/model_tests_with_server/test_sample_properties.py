import os

import pytest

from pydent.models import AquariumModelError
import functools

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
    parent = session.Sample.one(query={"sample_type_id": yeast_strain.id})
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


@pytest.mark.record_mode('no')
def test_update_properties(session):
    yeast_strain = session.SampleType.find_by_name("Yeast Strain")
    yeast = session.Sample.new(sample_type_id=yeast_strain.id,
                                   properties={
                                       "QC_length": 200,
                                       "Comp_cell_limit": "Yes"
                                   }
                               )
    parent = session.Sample.one(query={"sample_type_id": yeast_strain.id})
    yeast.update_properties({"Mating Type": "MATa", "Parent": parent, "QC_length": 100})

    assert yeast.properties["Mating Type"] == "MATa"
    assert yeast.properties["Parent"] == parent
    assert yeast.properties["QC_length"] == 100


class TestUpdateFieldValueArrays:
    """Tests for updating field_values that are arrays."""

    SAMPLE_TYPE_NAME = 'Fragment'
    FIELD_TYPE_NAME = 'Fragment Mix Array'

    @pytest.fixture(scope='module')
    def example_sample_type(self, session):
        sample_type = session.SampleType.find_by_name(self.SAMPLE_TYPE_NAME)
        assert sample_type
        return sample_type


    @pytest.fixture(scope='function')
    def example_sample(self, session, example_sample_type):
        sample = session.Sample.one(query=dict(sample_type_id=example_sample_type.id))
        assert sample
        return sample

    @pytest.fixture(scope='module')
    def get_samples(self, session, example_sample_type):
        """Returns a function that queries for samples that match the field_value of the FieldValue array specified
        in the default values above. These samples can be used to set the properties for the tests."""
        allowable_field_types = example_sample_type.field_type(self.FIELD_TYPE_NAME).allowable_field_types
        assert allowable_field_types
        aft = allowable_field_types[0]

        func = functools.partial(session.Sample.last, query=dict(sample_type_id=aft.sample_type_id))
        return func

    @pytest.mark.parametrize('test_server_changes', [False, True])
    @pytest.mark.parametrize('num_field_values', [2])
    # @pytest.mark.parametrize("num_field_values", list(range(10)), ids=["{} field values".format(x) for x in range(10)])
    def test_local_changes(self, session, num_field_values, example_sample, get_samples, test_server_changes):

        value_samples = get_samples(num_field_values)
        assert len(value_samples) == num_field_values
        example_sample.update_properties({
            self.FIELD_TYPE_NAME: get_samples(num_field_values)
        })

        assert len(example_sample.field_value_array(self.FIELD_TYPE_NAME)) == num_field_values
        assert len(example_sample.properties[self.FIELD_TYPE_NAME]) == num_field_values

        if test_server_changes:
            if example_sample.id:
                example_sample.update()
            else:
                example_sample.save()

            fvs_from_server = session.FieldValue.where({'parent_id': example_sample.id, 'name': self.FIELD_TYPE_NAME,
                                                        'parent_class': 'Sample'})
            assert len(fvs_from_server) == num_field_values

# @pytest.mark.parametrize("num_field_values", list(range(10)), ids=["{} field values".format(x) for x in range(10)])
def test_update_properties_using_array(session, num_field_values):
    """Test updating a sample properties array. Requires a 'Fragment' SampleType in the database with a 'Fragment Mix Array'
    FieldType."""

    # grab example Fragment
    fragment_type = session.SampleType.find_by_name("Fragment")
    sample = session.Sample.one(query=dict(sample_type_id=fragment_type.id))

    # query an array of additional Fragments
    if num_field_values == 0:
        fragments = []
    else:
        fragments = session.Sample.last(num_field_values, query=dict(sample_type_id=fragment_type.id))

    # update the sample properties with fragments
    sample.update_properties({
        "Fragment Mix Array": fragments,
        "Length": 1000
    })

    # verify local changes
    assert len(sample.field_value_array("Fragment Mix Array")) == len(fragments)
    assert set([s.id for s in sample.properties['Fragment Mix Array']]) == set([s.id for s in fragments])
    assert sample.properties["Length"] == 1000

    # verify server changes
    reloaded = session.Sample.find(sample.id)
    assert len(reloaded.properties['Fragment Mix Array']) == len(fragments)

    # update the sample properties again
    new_set_fragments = session.Sample.last(10-num_field_values, query=dict(sample_type_id=fragment_type.id))
    sample.update_properties({
        "Fragment Mix Array": new_set_fragments,
        "Length": 1100
    })

    # verify local changes
    assert len(sample.field_value_array("Fragment Mix Array")) == len(new_set_fragments)
    assert set([s.id for s in sample.properties['Fragment Mix Array']]) == set([s.id for s in new_set_fragments])
    assert sample.properties["Length"] == 1100
