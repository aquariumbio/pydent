"""Budgets"""

import aq

class BudgetRecord(aq.Record):

    """BudgetRecord used to define a budget"""

    def __init__(self, model, data):
        """Make a new BudgetRecord"""
        super(BudgetRecord, self).__init__(model, data)
        self.has_many("user_budget_associations", aq.UserBudgetAssociation)


class BudgetModel(aq.Base):

    """BudgetModel class, generates BudgetRecords"""

    def __init__(self):
        """Make a new BudgetModel"""
        super(BudgetModel, self).__init__("Budget")


Budget = BudgetModel()
