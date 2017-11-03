import aq

class ItemRecord(aq.Record):
    def __init__(self,model,data):
        super(ItemRecord,self).__init__(model,data)
        self.has_one("sample", aq.Sample)
        self.has_one("object_type", aq.ObjectType)
        self.has_many_generic("data_associations", aq.DataAssociation)

class ItemModel(aq.Base):
    def __init__(self):
        super(ItemModel,self).__init__("Item")

Item = ItemModel()
