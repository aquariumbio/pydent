import aq

class OperationTypeRecord(aq.Record):
    def __init__(self,model,data):
        super(OperationTypeRecord,self).__init__(model,data)

class OperationTypeModel(aq.Base):

    def __init__(self):
        super(OperationTypeModel,self).__init__("OperationType")

OperationType = OperationTypeModel()
