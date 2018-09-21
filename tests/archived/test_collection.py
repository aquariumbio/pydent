import json
import pytest
from pydent import models


@pytest.fixture
def example_collection(session, scope='module'):
    """
    this is a 96 well plate on Nursery (9/19/2018)
    """
    collections = session.Collection.where({'id': 389073})
    assert len(collections) == 1
    collection = next(iter(collections))
    assert collection
    return collection


class TestCollection:

    def get_part_associations(self, session, collection):
        part_associations = session.PartAssociation.where(
            {'collection_id': collection.id}
        )
        assert part_associations
        assert len(part_associations) > 0
        return part_associations

    def test_parts(self, session, example_collection):
        collection = example_collection
        part_associations = self.get_part_associations(session, collection)

        expected_part = next(iter([
            assoc.part for assoc in part_associations
            if assoc.row == 0 and assoc.column == 0]))

        assert collection.part(0, 0) is not None
        actual_part = collection.part(0, 0)
        assert expected_part.id == actual_part.id

    """def test_matrix(self, session, example_collection):
        collection = example_collection
        part_associations = self.get_part_associations(session, collection)

        matrix = list()
        for row in range(8):
            row_assoc = [assoc for assoc in part_associations
                         if assoc.row == row]
            row_list = list()
            for col in range(12):
                if

            matrix.append(row_list)

        print(json.dumps(matrix, indent=2))
        assert False"""
