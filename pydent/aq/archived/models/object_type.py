from pydent import aq


class ObjectTypeRecord(aq.Record):
    def __init__(self, model, data):
        super(ObjectTypeRecord, self).__init__(model, data)


class ObjectTypeModel(aq.Base):

    def __init__(self):
        super(ObjectTypeModel, self).__init__("ObjectType")


ObjectType = ObjectTypeModel()
