"""Group"""

import aq

class GroupRecord(aq.Record):

    """GroupRecord used to define a group of users"""

    def __init__(self, model, data):
        """Make a new GroupRecord"""
        super(GroupRecord, self).__init__(model, data)


class GroupModel(aq.Base):

    """GroupModel class, generates GroupRecords"""

    def __init__(self):
        """Make a new GroupModel"""
        super(GroupModel, self).__init__("Group")

Group = GroupModel()
