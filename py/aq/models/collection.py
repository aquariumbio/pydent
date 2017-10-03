import aq

class CollectionRecord(aq.Record):
    def __init__(self,model,data):
        super(CollectionRecord,self).__init__(model,data)
        self.has_one("object_type", aq.ObjectType)
        self.has_many_generic("data_associations", aq.DataAssociation)

class CollectionModel(aq.Base):

    def __init__(self):
        super(CollectionModel,self).__init__("Collection")

Collection = CollectionModel()
