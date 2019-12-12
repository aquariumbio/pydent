from uuid import uuid4

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
    ot = session.ObjectType.where("rows > 2 AND columns > 2")[0]
    return session.Collection.one(query={"object_type_id": ot.id})


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
        print(index)
        example_collection[:, :] = None
        expected = np.zeros(example_collection.dimensions)
        expected.__setitem__(index, 1)
        print(expected)
        example_collection.__setitem__(index, 1)
        print(example_collection.matrix)
        for r, c in zip(*np.where(expected == 1)):
            assert example_collection[r, c] == 1
        for r, c in zip(*np.where(expected != 1)):
            assert example_collection[r, c] != 1

        for pa in example_collection.part_associations:
            assert pa.part is example_collection.parts_matrix[pa.row, pa.column]


class TestCollectionSubmit:
    def test_submit(self, session):
        ot = session.ObjectType.where("rows > 1")[0]
        collection = session.Collection.new(object_type=ot)

        # set and save
        collection[0] = 1
        print(collection.matrix)
        print(collection.save())
        print(collection.id)
        print(collection.matrix)
        assert collection[0] == [1] * (ot.columns)
        assert collection[1] == [None] * (ot.columns)
        loaded = session.Collection.find(collection.id)
        assert loaded[0] == [1] * (ot.columns)
        assert loaded[1] == [None] * (ot.columns)

        # set and save new row
        collection[1] = 2
        collection.save()
        print(collection.matrix)
        assert collection[0] == [1] * (ot.columns)
        assert collection[1] == [2] * (ot.columns)
        loaded = session.Collection.find(collection.id)
        assert loaded[0] == [1] * (ot.columns)
        assert loaded[1] == [2] * (ot.columns)

        # overwrite existing part
        collection[0, 0] = 3
        assert collection[0, 0] == 3
        assert collection[0, 1:] == [1] * (ot.columns - 1)
        assert collection[1] == [2] * (ot.columns)

        collection.save()
        assert collection[0, 0] == 3
        assert collection[0, 1:] == [1] * (ot.columns - 1)
        assert collection[1] == [2] * (ot.columns)

        loaded = session.Collection.find(collection.id)
        assert loaded[0, 0] == 3
        assert loaded[0, 1:] == [1] * (ot.columns - 1)
        assert loaded[1] == [2] * (ot.columns)


class TestCollectionAssociate:
    def test_associate_raises_value_error(self, session):
        ot = session.ObjectType.where("rows > 1")[0]
        collection = session.Collection.new(object_type=ot)

        with pytest.raises(ValueError):
            collection.data_matrix[0] = ("idk", 1)

    def test_associate_single_sample(self, session):
        ot = session.ObjectType.where("rows > 1")[0]
        collection = session.Collection.new(object_type=ot)
        collection[0] = 1
        collection.data_matrix[0] = {"idk": 1}
        assert collection.data_matrix[0, 1] == {"idk": 1}
        collection.data_matrix[0, -1] = {"idk": 2}
        assert collection.data_matrix[0, -1] == {"idk": 2}

    def test_associate_single_sample(self, session):
        ot = session.ObjectType.where("rows > 1")[0]
        collection = session.Collection.new(object_type=ot)
        collection[0] = 1
        val1 = str(uuid4())
        val2 = str(uuid4())
        collection.data_matrix[0] = {"key": val1}

        print(collection.parts_matrix)

        for pa in collection.part_associations:
            # print(pa.part)
            # print(collection.parts_matrix[pa.row, pa.column])
            assert pa.part is collection.parts_matrix[pa.row, pa.column]

        collection.part_association_matrix

        # save on server
        assert collection.parts_matrix[0, 0].data_associations
        print(collection.parts_matrix[0, 0].data_associations[0])
        collection.save()
        collection = session.Collection.find(collection.id)
        assert collection.parts_matrix[0, 0].data_associations
        print(collection.parts_matrix[0, 0].data_associations[0])
        assert collection.data_matrix[0, 0] == {"key": val1}

        # 1st load
        loaded_collection = session.Collection.find(collection.id)
        assert loaded_collection.parts_matrix[0, 0].data_associations
        assert loaded_collection.data_matrix[0, 0] == {"key": val1}

        # update
        loaded_collection = session.Collection.find(collection.id)
        loaded_collection.data_matrix[0, 0] = {"key": val2}
        assert loaded_collection.parts_matrix[0, 0].data_associations
        assert loaded_collection.data_matrix[0, 0] == {"key": val2}

        # 2nd load
        loaded_collection2 = session.Collection.find(collection.id)
        assert loaded_collection2.parts_matrix[0, 0].data_associations
        assert loaded_collection2.data_matrix[0, 0] == {"key": val2}

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
