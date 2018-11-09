from pydent.models import Item

def test_item_get_data_association(fake_session):
    item = fake_session.Item.load(
        {'created_at': '2018-07-03T13:06:35-07:00',
         'data': '{"matrix": [[23853, 23853, 23853, 23846, 23846, 23846], [-1, -1, -1, -1, -1, -1], [-1, -1, -1, -1, -1, -1], [-1, -1, -1, -1, -1, -1]]}',
         'data_associations': [{'id': 199866,
                                'key': 'key0',
                                'object': '{"key0": "hello"}',
                                'parent_class': 'Item',
                                'parent_id': 141572,
                                'rid': 3,
                                'updated_at': '2018-07-03T14:40:38-07:00',
                                'upload_id': None},
                               {
                                   'id': 1235,
                                   'key': 'key1',
                                   'object': '{"key1": [1,2,3,4]}',
                                   'parent_class': 'Item',
                                   'parent_id': 141572,
                                   'rid': 3,
                                   'updated_at': '2018-07-03T14:40:38-07:00',
                                   'upload_id': None},
                               {
                                   'id': 12356,
                                   'key': 'key1',
                                   'object': '{"key1": [2,2,3,4]}',
                                   'parent_class': 'Item',
                                   'parent_id': 141572,
                                   'rid': 3,
                                   'updated_at': '2018-07-03T14:40:38-07:00',
                                   'upload_id': None},
                               ],
         'id': 141572,
         'inuse': -1,
         'location': 'deleted',
         'locator_id': None,
         'object_type_id': 789,
         'quantity': -1,
         'rid': 1,
         'sample_id': None,
         'updated_at': '2018-07-03T14:40:38-07:00'})

    assert item.get('key0') == 'hello'
    assert item.get('key1') == [[1,2,3,4], [2,2,3,4]]
    assert not hasattr(item, "locator_id")

    item.locator_id = 5

    assert 'locator_id' not in item.dump()