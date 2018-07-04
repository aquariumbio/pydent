from pydent.models import Collection


def test_collection_matrix():
    c = Collection.load({'created_at': '2018-07-03T13:06:35-07:00',
                     'data': '{"matrix": [[23853, 23853, 23853, 23846, 23846, 23846], [-1, -1, -1, -1, -1, -1], [-1, -1, -1, -1, -1, -1], [-1, -1, -1, -1, -1, -1]]}',
                     'id': 141572,
                     'inuse': -1,
                     'location': 'deleted',
                     'locator_id': None,
                     'object_type_id': 789,
                     'quantity': -1,
                     'rid': 25,
                     'sample_id': None,
                     'updated_at': '2018-07-03T14:40:38-07:00'})
    expected_matrix = [[23853, 23853, 23853, 23846, 23846, 23846], [-1, -1, -1, -1, -1, -1], [-1, -1, -1, -1, -1, -1], [-1, -1, -1, -1, -1, -1]]
    assert c.data['matrix'] == expected_matrix
    assert c.matrix == expected_matrix
