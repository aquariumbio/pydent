from pydent import aq


class UserBudgetAssociationRecord(aq.Record):
    def __init__(self, model, data):
        super(UserBudgetAssociationRecord, self).__init__(model, data)
        self.has_one("budget", aq.Budget)
        self.has_one("user", aq.User)


class UserBudgetAssociationModel(aq.Base):

    def __init__(self):
        super(UserBudgetAssociationModel, self).__init__(
            "UserBudgetAssociation")


UserBudgetAssociation = UserBudgetAssociationModel()
