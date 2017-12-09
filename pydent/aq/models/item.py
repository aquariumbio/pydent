"""Item"""


import aq


class ItemRecord(aq.Record):

    """ItemRecord defines the basic information needed to keep track of
    inventory items.
    """

    def __init__(self, model, data):
        """Make a new ItemRecord"""
        super(ItemRecord, self).__init__(model, data)
        self.has_one("sample", aq.Sample)
        self.has_one("object_type", aq.ObjectType)
        self.has_many_generic("data_associations", aq.DataAssociation)


class ItemModel(aq.Base):

    """ItemModel class, generates ItemRecords"""

    def __init__(self):
        """Make a new ItemModel"""
        super(ItemModel, self).__init__("Item")


Item = ItemModel()
