from uuid import uuid4

import pytest


class TestDataAssociation:
    samples = None

    def get_example_item(self, session):
        if self.samples is None:
            samples = session.Sample.first(
                100, query={"user_id": session.current_user.id}
            )
            self.samples = samples
        for s in self.samples:
            if s.items:
                return s.items[0]
        raise Exception("Could not find item")

    @pytest.mark.record_mode("no")
    def test_successive_queries(self, session):
        """We expect the length of the associations to be unchanged.

        The 'where' query for data associations occasionally has strange
        behavior, retrieving only some of the data associations.
        """

        lengths = []
        for i in range(3):
            item1 = self.get_example_item(session)
            item_das1 = list(item1.data_associations)
            if len(item_das1) not in lengths:
                lengths.append(len(item_das1))
        assert len(lengths) == 1

    @pytest.mark.record("no")
    def test_create_data_association(self, session):

        item = self.get_example_item(session)
        val = str(uuid4())
        new_da = item.associate("test", val)

        # check data association got id
        print(new_da.id)
        assert new_da.id
        assert new_da.parent_id == item.id
        assert new_da.parent_class == "Item"
        assert new_da in item.data_associations
        assert new_da.value == val

        # check server was updated
        loaded = session.DataAssociation.find(new_da.id)
        assert loaded.value == val

    @pytest.mark.record("no")
    def test_update_data_association(self, session):

        item = self.get_example_item(session)

        key = str(uuid4())
        val1 = str(uuid4())
        val2 = str(uuid4())

        assert not item.get_data_association(key)

        new_da = item.associate(key, val1)

        assert new_da.id
        assert new_da.parent_id == item.id
        assert new_da.parent_class == "Item"
        assert new_da in item.data_associations

        # check server was updated
        loaded = session.DataAssociation.find(new_da.id)
        assert loaded.value == val1

        # update data association
        new_da2 = item.associate(key, val2)
        assert new_da2.id == new_da.id
        assert new_da2.value == val2

        # check server was updated
        loaded = session.DataAssociation.find(new_da2.id)
        assert loaded.value == val2

    @pytest.mark.record("no")
    def test_delete_data_association(self, session):

        item = self.get_example_item(session)

        val = str(uuid4())
        key = "test"
        item.associate(key, val)
        das = item.get_data_associations(key)
        assert das

        for da in das:
            da.delete()

        item.reset_field("data_associations")
        das = item.get_data_associations(key)
        assert not das

    @pytest.mark.record("no")
    def test_delete_data_associations(self, session):

        item = self.get_example_item(session)

        val = str(uuid4())
        key = "test"
        item.associate(key, val)
        das = item.get_data_associations(key)
        assert das

        item.delete_data_associations(key)

        das = item.get_data_associations(key)
        assert not das
