import json

import numpy as np
import pytest


@pytest.fixture
def example_part_association(session):
    """An example part association."""
    part_association = session.PartAssociation.one()
    return part_association


@pytest.fixture
def example_collection(session, example_part_association):
    """An example collection.

    Supposed to have a part
    """
    return example_part_association.collection


class TestCollection:
    def test_part_method(self, session, example_collection):
        """We expect .part(r, c) to retrieve a part."""
        collection = example_collection
        part_associations = collection.part_associations

        # the part associations have been deserialized
        # therefore, part(row, col) should return exactly the part
        part_association = part_associations[0]
        expected_part = part_association.part
        row = part_association.row
        col = part_association.column
        assert collection.part(row, col) is expected_part

    def test_part_retrieval_from_server(self, session, example_collection):
        """We expect .part(r, c) to retrieve a part from the server."""
        collection = example_collection
        part_associations = collection.part_associations

        # the part associations have been deserialized
        # therefore, part(row, col) should return exactly the part
        part_association = part_associations[0]
        row = part_association.row
        col = part_association.column
        expected_part = part_association.part

        # now we will remove the cached data and re-retrieve it
        # from the server by calling the .part method.
        collection.reset_field("part_associations")
        assert not collection.is_deserialized("part_associations")
        retrieved_part = collection.part(row, col)
        assert retrieved_part.id == expected_part.id
        assert retrieved_part is not expected_part

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


class Slicer:
    def __getitem__(self, item):
        return item


slicer = Slicer()


class TestCollectionSetter:
    @pytest.mark.parametrize(
        "index",
        [
            slicer[0],
            slicer[1],
            slicer[:3],
            slicer[:, :3],
            slicer[1, :3],
            slicer[:, -3:],
            slicer[1, -3:],
            slicer[:3, :],
            slicer[:3, 1],
            slicer[-3:, :],
            slicer[-3:, 1],
            slicer[:3, :2],
            slicer[-3:, -2:],
            slicer[:, :],
        ],
    )
    def test_set_rc(self, session, example_collection, index):
        expected = np.zeros(example_collection.dimensions)
        expected.__setitem__(index, 1)

        example_collection.__setitem__(index, 1)
        for r, c in zip(*np.where(expected == 1)):
            assert example_collection[r, c] == 1
        for r, c in zip(*np.where(expected != 1)):
            assert example_collection[r, c] != 1


class TestCollectionSubmit:
    def test_submit(self, session):
        ot = session.ObjectType.where("rows > 1")[0]
        collection = session.Collection.new(object_type=ot)

        collection[0] = 1

        print(collection.matrix)
        print(collection.save())
        print(collection.id)
        print(collection.matrix)

        # sample_type = session.SampleType.find(1)
        # object_type = session.ObjectType.where({'sample_type_id': sample_type.id})[0]
        #
        # collection[1, 0] = 2
        # collection.location = 'test'
        # collection.save()
        #
        # print(collection.matrix)
        # item = session.Item.new(
        #     object_type=object_type,
        #     sample=sample_type.samples[0]
        # )
        # item.save()
        # print(item.id)
