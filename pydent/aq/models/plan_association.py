"""Plan Association"""

import aq


class PlanAssociationRecord(aq.Record):
    """PlanAssociationRecord is a join table that associations plans with
    operations
    """

    def __init__(self, model, data):
        """Make a new PlanAssociationRecord"""
        super(PlanAssociationRecord, self).__init__(model, data)
        self.has_one("plan", aq.Plan)
        self.has_one("operation", aq.Operation)


class PlanAssociationModel(aq.Base):

    """PlanAssociationModel class, generates PlanAssociationRecords"""

    def __init__(self):
        """Make a new PlanAssociationModel"""
        super(PlanAssociationModel, self).__init__("PlanAssociation")


PlanAssociation = PlanAssociationModel()
