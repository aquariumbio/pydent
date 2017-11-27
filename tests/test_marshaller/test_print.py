import pytest
from pydent.marshaller import MarshallerBase, add_schema, Relation

def test_marshallerbase_print():

    @add_schema
    class Author(MarshallerBase):
        fields = dict(
            books=Relation("Book", many=True, callback="get_books", params=())
        )

        def __init__(self, x=None):
            self.x = x

        def get_books(self):
            pass

    a = Author()
    print(a)