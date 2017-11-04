"""JobAssociation"""

import aq

class JobAssociationRecord(aq.Record):

    """JobAssociationRecord is a join table for jobs and their operations"""

    def __init__(self, model, data):
        """Make a new JobAssociationRecord"""
        super(JobAssociationRecord, self).__init__(model, data)
        self.has_one("job", aq.Job)
        self.has_one("operation", aq.Operation)


class JobAssociationModel(aq.Base):

    """JobAssociationModel class, generates JobAssociationRecords"""

    def __init__(self):
        """Make a new JobAssociationModel"""
        super(JobAssociationModel, self).__init__("JobAssociation")


JobAssociation = JobAssociationModel()
