from uuid import uuid4
import pytest
import time


def search(session, model_class, func, query=None, step_multiply=10, terminate=3, reverse=True):
    interface = session.model_interface(model_class)
    if reverse:
        search_func = interface.last
    else:
        search_func = interface.first
    limit = 1
    offset = 0
    step = 1

    while step < terminate:
        models = search_func(limit, query=query, opts={'reverse': reverse, 'offset': offset})
        found_models = [m for m in models if func(m)]
        if found_models:
            return found_models

        offset += len(models)
        limit *= step_multiply
        step += 1
    return None


@pytest.fixture
def example_item(session):
    items = search(session, 'Item', lambda m: m.data_associations)
    return items[0]


def test_assert_parent_class_of_item_association(session, example_item):
    for da in example_item.data_associations:
        assert da.parent_class == 'Item'


def test_data_association_bug(session):

    item1 = session.Item.last()[0]
    item2 = session.Item.find(item1.id)

    assert len(item1.data_associations) == len(item2.data_associations)

class TestDataAssociation:

    def get_example_item(self, session):
        return lambda: session.Item.one(first=True)

    def test_successive_queries(self, session):
        """We expect the length of the associations to be unchanged. The 'where' query for
        data associations occasionally has strange behavior, retrieving only some of the data
        associations."""

        lengths = []
        for i in range(5):
            item1 = self.get_example_item(session)()
            item_das1 = list(item1.data_associations)
            if len(item_das1) not in lengths:
                lengths.append(len(item_das1))
        assert len(lengths) == 1

    def test_create_data_association(self, session):

        item = self.get_example_item(session)()
        item_das = item.data_associations

        val = str(uuid4())
        item.associate('test', val)

        reloaded = self.get_example_item(session)()
        item_das_reloaded = reloaded.data_associations

        assert len(item_das_reloaded) == len(item_das) + 1

