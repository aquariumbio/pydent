import json

import pytest

from pydent.models import Collection
from pydent.models import PartAssociation


@pytest.fixture
def example_part_association(session):
    part_association = session.PartAssociation.one()
    return part_association


@pytest.fixture
def example_collection(session, example_part_association):
    return example_part_association.collection


class TestCollection:
    def test_parts(self, session, example_collection):
        collection = example_collection
        part_associations = collection.part_associations

        # TODO: this test is failing with StopIteration???

        expected_part = part_associations[0].part
        # expected_part = next(
        #     iter(
        #         [
        #             assoc.part
        #             for assoc in part_associations
        #             if assoc.row == 0 and assoc.column == 0
        #         ]
        #     )
        # )

        assert collection.part(0, 0) is not None
        actual_part = collection.part(0, 0)
        assert expected_part.id == actual_part.id

    def test_dimensions(self, session, example_collection):
        collection = example_collection
        assert collection.dimensions
        row, col = collection.dimensions
        assert row
        assert col

    def test_matrix(self, session, example_collection):
        collection = example_collection
        part_associations = collection.part_associations
        num_row, num_col = collection.dimensions

        expected_matrix = list()
        for row in range(num_row):
            row_assoc = [assoc for assoc in part_associations if assoc.row == row]
            row_list = list()
            for col in range(num_col):
                sample_id = None
                col_assoc = [assoc for assoc in row_assoc if assoc.column == col]
                if col_assoc:
                    assoc = next(iter(col_assoc))
                    sample_id = assoc.part.sample.id
                row_list.append(sample_id)
            expected_matrix.append(row_list)

        assert collection.matrix == expected_matrix
