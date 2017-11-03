from pydent import aq


class GroupRecord(aq.Record):
    def __init__(self, model, data):
        super(GroupRecord, self).__init__(model, data)


class GroupModel(aq.Base):

    def __init__(self):
        super(GroupModel, self).__init__("Group")


Group = GroupModel()
