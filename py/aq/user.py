import aq

class UserRecord(aq.Record):
    pass

class UserModel(aq.Base):

    def __init__(self):
        super(UserModel,self).__init__("User")

User = UserModel()
