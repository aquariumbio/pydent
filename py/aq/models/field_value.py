import aq

class FieldValueRecord(aq.Record):

    def __init__(self,model,data):
        super(FieldValueRecord,self).__init__(model,data)
        self.has_one("field_type", aq.FieldType)
        self.has_one("allowable_field_type", aq.AllowableFieldType)
        self.has_one("item",   aq.Item, opts={"reference": "child_item_id"})
        self.has_one("sample", aq.Sample, opts={"reference": "child_sample_id"})
        self.has_one("operation", aq.Operation, opts={"reference": "parent_id"})
        self.has_one("sample", aq.Sample, opts={"reference": "parent_id"})

class FieldValueModel(aq.Base):

    def __init__(self):
        super(FieldValueModel,self).__init__("FieldValue")

FieldValue = FieldValueModel()
