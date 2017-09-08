import aq

class UserRecord(aq.Record):
    def __init__(self,model,data):
        super(UserRecord,self).__init__(model,data)
        self.has_many("samples", aq.Sample)

class UserModel(aq.Base):

    def __init__(self):
        super(UserModel,self).__init__("User")

User = UserModel()
