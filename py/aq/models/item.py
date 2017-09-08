import aq

class ItemRecord(aq.Record):
    def __init__(self,model,data):
        super(ItemRecord,self).__init__(model,data)
        self.has_one("sample", aq.Sample)

class ItemModel(aq.Base):
    def __init__(self):
        super(ItemModel,self).__init__("Item")

Item = ItemModel()
