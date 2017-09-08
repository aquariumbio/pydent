import aq

class OperationRecord(aq.Record):
    def __init__(self,model,data):
        super(OperationRecord,self).__init__(model,data)

class OperationModel(aq.Base):

    def __init__(self):
        super(OperationModel,self).__init__("Operation")

Operation = OperationModel()
