"""User"""

import aq


class UserRecord(aq.Record):

    """UserRecord defines a user"""

    def __init__(self, model, data):
        """Make a new User"""
        super(UserRecord, self).__init__(model, data)
        self.has_many("samples", aq.Sample)
        self.has_many("user_budget_associations", aq.UserBudgetAssociation)
        self.has_many(
            "budgets", aq.Budget,
            opts={"through": aq.UserBudgetAssociation,
                  "association": "budget"})


class UserModel(aq.Base):

    """UserModel class, generates UserRecords"""

    def __init__(self):
        """Make a new UserModel"""
        super(UserModel, self).__init__("User")

    @property
    def current(self):
        """Get the currently logged in user"""
        result = aq.http.get('/json/current')
        return self.record(result)


User = UserModel()
