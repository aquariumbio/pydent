import aq


class PlanAssociationRecord(aq.Record):

    def __init__(self, model, data):
        super(PlanAssociationRecord, self).__init__(model, data)
        self.has_one("plan", aq.Plan)
        self.has_one("operation", aq.Operation)


class PlanAssociationModel(aq.Base):

    def __init__(self):
        super(PlanAssociationModel, self).__init__("PlanAssociation")


PlanAssociation = PlanAssociationModel()
