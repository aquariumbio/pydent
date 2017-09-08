import aq

class AllowableFieldTypeRecord(aq.Record):
    def __init__(self,model,data):
        super(AllowableFieldTypeRecord,self).__init__(model,data)

class AllowableFieldTypeModel(aq.Base):

    def __init__(self):
        super(AllowableFieldTypeModel,self).__init__("AllowableFieldType")

AllowableFieldType = AllowableFieldTypeModel()
