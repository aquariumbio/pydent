import pytest

from pydent.models import Collection
from pydent.models import Item
from pydent.models import PartAssociation


@pytest.fixture
def example_part_association(session):
    part_association = session.PartAssociation.one()
    return part_association


@pytest.fixture
def example_collection(session, example_part_association):
    return example_part_association.collection


@pytest.fixture
def example_part(session, example_part_association):
    return example_part_association.part


class TestCollectionsAndParts:
    def test_collection_as_item(self, example_collection):
        assert isinstance(example_collection, Collection)
        assert isinstance(example_collection.as_item(), Item)

    def test_is_part(self, example_part, example_collection):
        assert example_part.is_part
        assert not example_collection.as_item().is_part

    def test_containing_collection(self, example_part, example_collection):
        containing_collection = example_part.containing_collection
        assert containing_collection.id == example_collection.id
