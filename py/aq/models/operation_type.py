import aq

class OperationTypeRecord(aq.Record):
    def __init__(self,model,data):
        super(OperationTypeRecord,self).__init__(model,data)
        self.has_many("operations", aq.Operation)
        self.has_many_generic("field_types", aq.FieldType)

class OperationTypeModel(aq.Base):

    def __init__(self):
        super(OperationTypeModel,self).__init__("OperationType")

OperationType = OperationTypeModel()
