import aq

class PlanRecord(aq.Record):
    def __init__(self,model,data):
        super(PlanRecord,self).__init__(model,data)
        self.has_many_generic("data_associations", aq.DataAssociation)

class PlanModel(aq.Base):

    def __init__(self):
        super(PlanModel,self).__init__("Plan")

Plan = PlanModel()
