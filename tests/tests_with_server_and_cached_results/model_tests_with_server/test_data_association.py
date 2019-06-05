from uuid import uuid4
import pytest


class TestDataAssociation:
    samples = None

    def get_example_item(self, session):
        if self.samples is None:
            samples = session.Sample.last(100, query={'user_id': session.current_user.id})
            self.samples = samples
        for s in self.samples:
            if s.items:
                return s.items[0]

        return lambda: session.Item.one(first=True, query={'user_id': session.current_user.id})

    @pytest.mark.record_mode('no')
    def test_successive_queries(self, session):
        """We expect the length of the associations to be unchanged. The 'where' query for
        data associations occasionally has strange behavior, retrieving only some of the data
        associations."""

        lengths = []
        for i in range(3):
            item1 = self.get_example_item(session)
            item_das1 = list(item1.data_associations)
            if len(item_das1) not in lengths:
                lengths.append(len(item_das1))
        assert len(lengths) == 1

    @pytest.mark.record('no')
    def test_create_data_association(self, session):

        item = self.get_example_item(session)
        val = str(uuid4())
        new_da = item.associate('test', val)

        assert new_da.id
        assert new_da.parent_id == item.id
        assert new_da.parent_class == 'Item'
        assert new_da in item.data_associations

    @pytest.mark.record('no')
    def test_delete_data_association(self, session):

        item = self.get_example_item(session)

        val = str(uuid4())
        key = 'test'
        item.associate(key, val)
        das = item.get_data_associations(key)
        assert das

        for da in das:
            da.delete()

        item.data_associations = None
        das = item.get_data_associations(key)
        assert not das
