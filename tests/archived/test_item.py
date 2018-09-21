import pytest
from pydent.models import Collection, Item, PartAssociation


@pytest.fixture
def example_collection(session, scope='module'):
    """
    this is a 96 well plate on Nursery (9/19/2018)
    """
    items = session.Item.where({'id': 389073})
    assert len(items) == 1
    item = next(iter(items))
    assert item
    return item


@pytest.fixture
def example_part(session, example_collection, scope='module'):
    collection = example_collection.as_collection()
    item = collection.part(0, 0)
    assert item
    return item


class TestItem:

    def test_collection(self, session, example_collection):
        item = example_collection
        assert item.is_collection
        assert not item.is_part
        assert item.containing_collection is None
        assert isinstance(item.as_collection(), Collection)

    def test_part(self, session, example_part, example_collection):
        item = example_part
        assert not item.is_collection
        assert item.is_part

        actual_collection = item.containing_collection
        assert actual_collection
        expected_collection = example_collection.as_collection()
        assert actual_collection.id == expected_collection.id

    # TODO: need to test that part/collection methods behave on a regular item
