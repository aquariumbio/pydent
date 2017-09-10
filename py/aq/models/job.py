import aq

class JobRecord(aq.Record):

    def __init__(self,model,data):
        super(JobRecord,self).__init__(model,data)
        self.has_many("operations",
            aq.Operation,
            opts={"through": aq.JobAssociation, "association": "operation"})

class JobModel(aq.Base):

    def __init__(self):
        super(JobModel,self).__init__("Job")

Job = JobModel()
