"""User Buget Associations"""

import aq


class UserBudgetAssociationRecord(aq.Record):

    """UserBudgetAssociationRecord is a join table associating users with
    Budgets
    """

    def __init__(self, model, data):
        """Make a new UserBudgetAssociation"""
        super(UserBudgetAssociationRecord, self).__init__(model, data)
        self.has_one("budget", aq.Budget)
        self.has_one("user", aq.User)


class UserBudgetAssociationModel(aq.Base):

    """UserBudgetAssociationModel class, generates
    UserBudgetAssociationRecords
    """

    def __init__(self):
        """Make a new UserBudgetAssociationModel"""
        super(UserBudgetAssociationModel, self).__init__(
            "UserBudgetAssociation")


UserBudgetAssociation = UserBudgetAssociationModel()
