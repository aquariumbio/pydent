import aq

class FieldValueRecord(aq.Record):
    def __init__(self,model,data):
        super(FieldValueRecord,self).__init__(model,data)

class FieldValueModel(aq.Base):

    def __init__(self):
        super(FieldValueModel,self).__init__("FieldValue")

FieldValue = FieldValueModel()
