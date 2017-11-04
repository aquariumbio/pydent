"""Collections"""

import aq

class CollectionRecord(aq.Record):

    """CollectionRecord, is a kind of Item that contains a matrix of sample
    ids
    """

    def __init__(self, model, data):
        """Make a new CollectionRecord"""
        super(CollectionRecord, self).__init__(model, data)
        self.has_one("object_type", aq.ObjectType)
        self.has_many_generic("data_associations", aq.DataAssociation)


class CollectionModel(aq.Base):

    """CollectionModel class, generates CollectionRecords"""

    def __init__(self):
        """Make a new CollectionModel"""
        super(CollectionModel, self).__init__("Collection")

Collection = CollectionModel()
