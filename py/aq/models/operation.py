import aq

class OperationRecord(aq.Record):

    def __init__(self,model,data):
        super(OperationRecord,self).__init__(model,data)
        self.has_many_generic("field_values", aq.FieldValue)
        self.has_many_generic("data_associations", aq.DataAssociation)
        self.has_one("operation_type", aq.OperationType)
        self.has_many("jobs",
            aq.Job,
            { "through": aq.JobAssociation, "association": "job"})

class OperationModel(aq.Base):

    def __init__(self):
        super(OperationModel,self).__init__("Operation")

Operation = OperationModel()
