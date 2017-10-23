from pydent import aq


class JobAssociationRecord(aq.Record):
    def __init__(self,model,data):
        super(JobAssociationRecord,self).__init__(model,data)
        self.has_one("job", aq.Job)
        self.has_one("operation", aq.Operation)

class JobAssociationModel(aq.Base):

    def __init__(self):
        super(JobAssociationModel,self).__init__("JobAssociation")

JobAssociation = JobAssociationModel()
