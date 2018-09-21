import pytest

from pydent.marshaller import add_schema, MarshallerBase, fields
from pydent.utils import pprint


@pytest.fixture(scope="function")
def author():
    @add_schema
    class Author(MarshallerBase):
        fields = dict(
            books=fields.Relation("Book", many=True, callback="get_books",
                                  callback_args=()),
            publisher=fields.Relation("Publisher", None, None, many=False),
        )

        def get_books(self):
            pass

    @add_schema
    class Publisher(MarshallerBase):
        fields = dict(
            meta=fields.Relation("PublisherMeta", callback=None, callback_args=None)
        )

    @add_schema
    class PublisherMeta(MarshallerBase):
        pass

    @add_schema
    class BookMetaData(MarshallerBase):
        pass

    @add_schema
    class Book(MarshallerBase):
        fields = dict(
            author=fields.Relation("Author", callback="get_author", callback_args=()),
            meta=fields.Relation("BookMetaData", callback=None, callback_args=None)
        )

    author_data = {
        "name": "Fyodor Dostoevsky",
        "books": [
            {
                "title": "Demons",
                "year": 1871,
                "meta": {"data": 5}
            },
            {
                "title": "The Idiot",
                "year": 1868,
                "meta": {'data': 6}
            }
        ],
        "publisher": {"name": "Penguin", 'meta': {'data': 88}}
    }

    return Author.load(author_data)


def test_with_no_relations(author):
    author.dump()
    author.dump(include={'books'})

    # no relations
    assert author.dump() == {"name": "Fyodor Dostoevsky"}


def test_with_one(author):
    # include 'books'
    assert author.dump(include={'books'}) == {
        "name": "Fyodor Dostoevsky",
        "books": [{"title": "Demons", "year": 1871, },
                  {"title": "The Idiot", "year": 1868, }]}

    # include 'publisher'
    adata = author.dump(include={"publisher"})
    pprint(adata)
    assert adata == {
        "name": "Fyodor Dostoevsky",
        "publisher": {"name": "Penguin"}
    }


def test_nested_with_one(author):
    assert author.dump(include={"publisher": {"meta"}}) == {
        "name": "Fyodor Dostoevsky",
        "publisher": {"name": "Penguin", 'meta': {'data': 88}}
    }


def test_with_many(author):
    """Relation keys can be a str, list, tuple, set or dictionary"""
    key = 'books'
    a1 = author.dump(include=key)
    assert a1 == author.dump(include={key})
    assert a1 == author.dump(include=(key,))
    assert a1 == author.dump(include={key: {}})

    assert a1 == {
        "name": "Fyodor Dostoevsky",
        "books": [
            {
                "title": "Demons",
                "year": 1871,
            },
            {
                "title": "The Idiot",
                "year": 1868,
            }
        ]}


def test_nested_with_many(author):
    # include 'books'
    assert author.dump(include={'books'}) == {
        "name": "Fyodor Dostoevsky",
        "books": [{"title": "Demons", "year": 1871, },
                  {"title": "The Idiot", "year": 1868, }]}

    # include 'books' with 'meta'
    adata = author.dump(include={"books": {"meta"}})
    pprint(adata)
    assert adata == {
        "name": "Fyodor Dostoevsky",
        "books": [
            {
                "title": "Demons",
                "year": 1871,
                "meta": {"data": 5}
            },
            {
                "title": "The Idiot",
                "year": 1868,
                "meta": {'data': 6}
            }
        ]
    }


def test_include_opts(author):
    adata = author.dump(
        include={
            "books": {
                "meta": {},
                'opts':
                    {'only': 'title'}
            }
        }
    )
    pprint(adata)
    assert adata == {"name": "Fyodor Dostoevsky", 'books': [
        {"title": "Demons", "meta": {"data": 5}},
        {'title': "The Idiot", "meta": {'data': 6}}
    ]}
