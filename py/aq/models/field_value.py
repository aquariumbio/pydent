import aq

class FieldValueRecord(aq.Record):

    def __init__(self,model,data):
        super(FieldValueRecord,self).__init__(model,data)
        self.has_one("item",   aq.Item, opts={"reference": "child_item_id"})
        self.has_one("sample", aq.Sample, opts={"reference": "child_sample_id"})

class FieldValueModel(aq.Base):

    def __init__(self):
        super(FieldValueModel,self).__init__("FieldValue")

FieldValue = FieldValueModel()
