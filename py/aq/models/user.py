import aq

class UserRecord(aq.Record):

    def __init__(self,model,data):
        super(UserRecord,self).__init__(model,data)
        self.has_many("samples", aq.Sample)
        self.has_many("user_budget_associations", aq.UserBudgetAssociation)
        self.has_many(
            "budgets", aq.Budget,
            opts={"through": aq.UserBudgetAssociation,
                  "association": "budget"})

class UserModel(aq.Base):

    def __init__(self):
        super(UserModel,self).__init__("User")

    @property
    def current(self):
        r = aq.http.get('/json/current')
        return self.record(r)

User = UserModel()
