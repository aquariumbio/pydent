import aq

class UserBudgetAssociationRecord(aq.Record):
    def __init__(self,model,data):
        super(UserBudgetAssociationRecord,self).__init__(model,data)

class UserBudgetAssociationModel(aq.Base):

    def __init__(self):
        super(UserBudgetAssociationModel,self).__init__("UserBudgetAssociation")

UserBudgetAssociation = UserBudgetAssociationModel()
