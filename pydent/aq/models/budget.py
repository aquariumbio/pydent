import aq


class BudgetRecord(aq.Record):
    def __init__(self, model, data):
        super(BudgetRecord, self).__init__(model, data)
        self.has_many("user_budget_associations", aq.UserBudgetAssociation)


class BudgetModel(aq.Base):

    def __init__(self):
        super(BudgetModel, self).__init__("Budget")


Budget = BudgetModel()
