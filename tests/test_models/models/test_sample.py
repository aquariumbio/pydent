import pytest


@pytest.fixture(scope="function")
def fake_sample(fake_session):
    sample_data = {
        'user_id': 192,
        'data': None,
        'sample_type_id': 4,
        'name': 'pSNR52_sgpCUP1-8_tracrRNA_2xCOM_tSUP4-TP',
        'id': 19763,
        'created_at': '2018-10-25T11:35:26.000-07:00',
        'description': 'An a sgRNA cassette that recognizes sgpCUP1-8 and has the 2xCOM amptamer.',
        'updated_at': '2018-10-25T11:35:26.000-07:00',
        'project': 'LightSwitch',
        'sample_type': {
            'name': 'Fragment',
            'description': 'A linear double stranded piece of DNA from PCR or Restriction Digest',
            'updated_at': '2015-11-29T07:55:20.000-08:00',
            'created_at': '2013-10-16T14:33:41.000-07:00',
            'id': 4,
            'field_types': [
                {
                    'choices': None,
                    'name': 'Sequence',
                    'required': True,
                    'parent_id': 4,
                    'preferred_operation_type_id': None,
                    'ftype': 'url',
                    'updated_at': '2016-05-09T21:17:39.000-07:00',
                    'routing': None,
                    'preferred_field_type_id': None,
                    'array': False,
                    'created_at': '2016-05-09T20:40:31.000-07:00',
                    'id': 11,
                    'role': None,
                    'part': None,
                    'parent_class': 'SampleType',
                    'allowable_field_types': [],
                    'rid': 34
                },
                {
                    'choices': None,
                    'name': 'Length',
                    'required': True,
                    'parent_id': 4,
                    'preferred_operation_type_id': None,
                    'ftype': 'number',
                    'updated_at': '2016-05-09T21:17:39.000-07:00',
                    'routing': None,
                    'preferred_field_type_id': None,
                    'array': False,
                    'created_at': '2016-05-09T20:40:31.000-07:00',
                    'id': 12,
                    'role': None,
                    'part': None,
                    'parent_class': 'SampleType',
                    'allowable_field_types': [],
                    'rid': 35
                },
                {
                    'choices': None,
                    'name': 'Template',
                    'required': False,
                    'parent_id': 4,
                    'preferred_operation_type_id': None,
                    'ftype': 'sample',
                    'updated_at': '2016-05-12T19:07:59.000-07:00',
                    'routing': None,
                    'preferred_field_type_id': None,
                    'array': False,
                    'created_at': '2016-05-09T20:40:31.000-07:00',
                    'id': 13,
                    'role': None,
                    'part': None,
                    'parent_class': 'SampleType',
                    'allowable_field_types': [
                        {
                            'sample_type_id': 2,
                            'object_type_id': None,
                            'updated_at': '2016-05-09T20:40:31.000-07:00',
                            'created_at': '2016-05-09T20:40:31.000-07:00',
                            'id': 2,
                            'field_type_id': 13,
                            'rid': 10
                        },
                        {
                            'sample_type_id': 3,
                            'object_type_id': None,
                            'updated_at': '2016-05-09T20:40:31.000-07:00',
                            'created_at': '2016-05-09T20:40:31.000-07:00',
                            'id': 3,
                            'field_type_id': 13,
                            'rid': 11
                        },
                        {
                            'sample_type_id': 4,
                            'object_type_id': None,
                            'updated_at': '2016-05-09T20:40:31.000-07:00',
                            'created_at': '2016-05-09T20:40:31.000-07:00',
                            'id': 4,
                            'field_type_id': 13,
                            'rid': 12
                        },
                        {
                            'sample_type_id': 5,
                            'object_type_id': None,
                            'updated_at': '2016-05-09T20:40:31.000-07:00',
                            'created_at': '2016-05-09T20:40:31.000-07:00',
                            'id': 5,
                            'field_type_id': 13,
                            'rid': 13
                        }
                    ],
                    'rid': 36
                },
                {
                    'choices': None,
                    'name': 'Forward Primer',
                    'required': False,
                    'parent_id': 4,
                    'preferred_operation_type_id': None,
                    'ftype': 'sample',
                    'updated_at': '2016-05-12T19:07:59.000-07:00',
                    'routing': None,
                    'preferred_field_type_id': None,
                    'array': False,
                    'created_at': '2016-05-09T20:40:31.000-07:00',
                    'id': 14,
                    'role': None,
                    'part': None,
                    'parent_class': 'SampleType',
                    'allowable_field_types': [
                        {
                            'sample_type_id': 1,
                            'object_type_id': None,
                            'updated_at': '2016-05-09T20:40:31.000-07:00',
                            'created_at': '2016-05-09T20:40:31.000-07:00',
                            'id': 6,
                            'field_type_id': 14,
                            'rid': 16
                        },
                        {
                            'sample_type_id': 4,
                            'object_type_id': None,
                            'updated_at': '2018-10-16T11:08:52.000-07:00',
                            'created_at': '2018-10-16T11:08:52.000-07:00',
                            'id': 5478,
                            'field_type_id': 14,
                            'rid': 17
                        }
                    ],
                    'rid': 37
                },
                {
                    'choices': None,
                    'name': 'Reverse Primer',
                    'required': False,
                    'parent_id': 4,
                    'preferred_operation_type_id': None,
                    'ftype': 'sample',
                    'updated_at': '2016-05-12T19:07:59.000-07:00',
                    'routing': None,
                    'preferred_field_type_id': None,
                    'array': False,
                    'created_at': '2016-05-09T20:40:31.000-07:00',
                    'id': 15,
                    'role': None,
                    'part': None,
                    'parent_class': 'SampleType',
                    'allowable_field_types': [
                        {
                            'sample_type_id': 1,
                            'object_type_id': None,
                            'updated_at': '2016-05-09T20:40:31.000-07:00',
                            'created_at': '2016-05-09T20:40:31.000-07:00',
                            'id': 7,
                            'field_type_id': 15,
                            'rid': 20
                        },
                        {
                            'sample_type_id': 4,
                            'object_type_id': None,
                            'updated_at': '2018-10-16T11:08:52.000-07:00',
                            'created_at': '2018-10-16T11:08:52.000-07:00',
                            'id': 5479,
                            'field_type_id': 15,
                            'rid': 21
                        }
                    ],
                    'rid': 38
                },
                {
                    'choices': None,
                    'name': 'Restriction Enzyme(s)',
                    'required': False,
                    'parent_id': 4,
                    'preferred_operation_type_id': None,
                    'ftype': 'string',
                    'updated_at': '2016-05-09T21:17:39.000-07:00',
                    'routing': None,
                    'preferred_field_type_id': None,
                    'array': False,
                    'created_at': '2016-05-09T20:40:31.000-07:00',
                    'id': 16,
                    'role': None,
                    'part': None,
                    'parent_class': 'SampleType',
                    'allowable_field_types': [],
                    'rid': 39
                },
                {
                    'choices': None,
                    'name': 'Yeast Marker',
                    'required': False,
                    'parent_id': 4,
                    'preferred_operation_type_id': None,
                    'ftype': 'string',
                    'updated_at': '2016-05-09T21:17:39.000-07:00',
                    'routing': None,
                    'preferred_field_type_id': None,
                    'array': False,
                    'created_at': '2016-05-09T20:40:31.000-07:00',
                    'id': 17,
                    'role': None,
                    'part': None,
                    'parent_class': 'SampleType',
                    'allowable_field_types': [],
                    'rid': 40
                },
                {
                    'choices': None,
                    'name': 'Fragment Mix Array',
                    'required': False,
                    'parent_id': 4,
                    'preferred_operation_type_id': None,
                    'ftype': 'sample',
                    'updated_at': '2018-10-23T20:25:42.000-07:00',
                    'routing': None,
                    'preferred_field_type_id': None,
                    'array': True,
                    'created_at': '2018-10-23T13:31:46.000-07:00',
                    'id': 16032,
                    'role': None,
                    'part': None,
                    'parent_class': 'SampleType',
                    'allowable_field_types': [
                        {
                            'sample_type_id': 1,
                            'object_type_id': None,
                            'updated_at': '2018-10-23T13:31:46.000-07:00',
                            'created_at': '2018-10-23T13:31:46.000-07:00',
                            'id': 5521,
                            'field_type_id': 16032,
                            'rid': 24
                        },
                        {
                            'sample_type_id': 4,
                            'object_type_id': None,
                            'updated_at': '2018-10-23T13:31:46.000-07:00',
                            'created_at': '2018-10-23T13:31:46.000-07:00',
                            'id': 5522,
                            'field_type_id': 16032,
                            'rid': 25
                        }
                    ],
                    'rid': 41
                }
            ],
            'rid': 5
        },
        'rid': 3
    }

    return fake_session.Sample.load(sample_data)


@pytest.mark.parametrize("num_field_values", list(range(10)), ids=["{} field values".format(x) for x in range(10)])
def test_update_properties_of_field_value_array(fake_sample, num_field_values):
    # fake_sample.field_value_array
    fake_sample.set_field_value_array('Fragment Mix Array', [fake_sample] * num_field_values)
    assert len(fake_sample.field_values) == num_field_values

    # reset field values
    fake_sample.set_field_value_array('Fragment Mix Array', [fake_sample] * (10-num_field_values))
    assert len(fake_sample.field_values) == 10-num_field_values

@pytest.mark.parametrize("num_field_values", list(range(10)), ids=["{} field values".format(x) for x in range(10)])
def test_update_properties_using_array(fake_sample, num_field_values):
    # fake_sample.field_value_array
    fake_sample.update_properties({
        "Fragment Mix Array": [fake_sample] * num_field_values
    })
    assert len(fake_sample.field_values) == num_field_values

    # reset field values
    fake_sample.update_properties({
        "Fragment Mix Array": [fake_sample] * (10-num_field_values)
    })
    assert len(fake_sample.field_values) == 10-num_field_values

