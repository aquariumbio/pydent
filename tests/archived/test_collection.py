import json
import pytest
from pydent.models import Collection, PartAssociation


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


@pytest.fixture
def ex_part_associations(session, example_collection, scope='module'):
    collection = example_collection
    part_associations = session.PartAssociation.where(
        {'collection_id': collection.id}
    )
    assert part_associations
    assert len(part_associations) > 0
    return part_associations


class TestCollection:

    def test_parts(self, session, example_collection, ex_part_associations):
        collection = example_collection
        part_associations = ex_part_associations

        expected_part = next(iter([
            assoc.part for assoc in part_associations
            if assoc.row == 0 and assoc.column == 0]))

        assert collection.part(0, 0) is not None
        actual_part = collection.part(0, 0)
        assert expected_part.id == actual_part.id

    def test_dimensions(self, session, example_collection):
        collection = example_collection
        assert collection.dimensions
        row, col = collection.dimensions
        assert row == 8 and col == 12

    def test_matrix(self, session, example_collection, ex_part_associations):
        collection = example_collection
        part_associations = ex_part_associations
        num_row, num_col = collection.dimensions

        expected_matrix = list()
        for row in range(num_row):
            row_assoc = [
                assoc for assoc in part_associations if assoc.row == row]
            row_list = list()
            for col in range(num_col):
                sample_id = None
                col_assoc = [
                    assoc for assoc in row_assoc if assoc.column == col]
                if col_assoc:
                    assoc = next(iter(col_assoc))
                    sample_id = assoc.part.sample.id
                row_list.append(sample_id)
            expected_matrix.append(row_list)

        assert collection.matrix == expected_matrix
