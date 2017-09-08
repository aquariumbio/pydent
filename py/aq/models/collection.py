import aq

class CollectionRecord(aq.Record):
    def __init__(self,model,data):
        super(CollectionRecord,self).__init__(model,data)

class CollectionModel(aq.Base):

    def __init__(self):
        super(CollectionModel,self).__init__("Collection")

Collection = CollectionModel()
