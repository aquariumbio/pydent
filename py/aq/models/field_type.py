import aq

class FieldTypeRecord(aq.Record):
    def __init__(self,model,data):
        super(FieldTypeRecord,self).__init__(model,data)

class FieldTypeModel(aq.Base):

    def __init__(self):
        super(FieldTypeModel,self).__init__("FieldType")

FieldType = FieldTypeModel()
