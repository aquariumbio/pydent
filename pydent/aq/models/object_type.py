"""Object Type"""

import aq

class ObjectTypeRecord(aq.Record):

    """ObjectTypeRecord defines the container for an item"""

    def __init__(self, model, data):
        """Make a new ObjectTypeRecord"""
        super(ObjectTypeRecord, self).__init__(model, data)

class ObjectTypeModel(aq.Base):

    """ObjectTypeModel class, generates ObjectTypeRecords"""

    def __init__(self):
        """Make a new ObjectTypeModel"""
        super(ObjectTypeModel, self).__init__("ObjectType")

ObjectType = ObjectTypeModel()
