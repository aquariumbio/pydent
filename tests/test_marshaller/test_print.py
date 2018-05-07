import pytest
from pydent.marshaller import MarshallerBase, add_schema, fields


@pytest.fixture(scope='function')
def author():
    @add_schema
    class Author(MarshallerBase):
        fields = dict(
            books=fields.Relation(
                "Book", many=True, callback="get_books", params=())
        )

        def __init__(self, x=None):
            self.x = x

        def get_books(self, *args):
            pass

    return Author


def test_to_json(author):
    """Expect to return the fields & relationships"""
    author_data = {'name': 'JoeSmo'}
    a = author.load(author_data)

    a_json = a._to_dict()
    expected_data = dict(author_data)
    expected_data.update(a.relationships)
    assert a_json == expected_data


def test_to_json_with_value_for_relations(author):
    """Expect to return the fields + relationships.
    In cases where relationships exist, that value should be returned."""
    author_data = {'name': 'JoeSmo'}
    a = author.load(author_data)
    a.books = 5
    a_json = a._to_dict()
    expected_data = dict(author_data)
    expected_data.update({'books': 5})
    assert a_json == expected_data


# def test_to_json_pass_in_dump_args(author):
#     author_data = {'name': 'JoeSmo', 'id': 4}
#     a = author.load(author_data)
#     assert a._to_dict(only=('name',),
#           all_relations=False) == {'name': 'JoeSmo'}
#

def test_marshallerbase_print():

    @add_schema
    class Author(MarshallerBase):
        fields = dict(
            books=fields.Relation("Book", many=True,
                                  callback="get_books", params=())
        )

        def __init__(self, x=None):
            self.x = x

        def get_books(self, *args):
            pass

    a = Author()
    print(a)
